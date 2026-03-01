import argparse
import json
import math
import os
import random
import shutil
import subprocess
import sys
import tempfile
import traceback

from moviepy.editor import (
    AudioFileClip,
    ColorClip,
    CompositeAudioClip,
    CompositeVideoClip,
    ImageClip,
    VideoFileClip,
    concatenate_videoclips,
    vfx,
)


class GeneratorConfig:
    def __init__(
        self,
        source_folder,
        output_file,
        mode="STANDARD",
        clip_count=20,
        min_duration=0.5,
        max_duration=2.5,
        resolution="1280x720",
        enable_video_effects=True,
        enable_audio_effects=True,
        audio_library_folder="",
        output_format="mp4",
        bitrate="2500k",
        export_metadata=False,
        project_name="YTPGen Mega Project",
        bpm=120,
        temp_folder="",
        final_scale="",
    ):
        self.source_folder = source_folder
        self.output_file = output_file
        self.mode = (mode or "STANDARD").upper()
        self.clip_count = max(1, int(clip_count))
        self.min_duration = max(0.1, float(min_duration))
        self.max_duration = max(self.min_duration, float(max_duration))
        self.resolution = resolution
        self.enable_video_effects = bool(enable_video_effects)
        self.enable_audio_effects = bool(enable_audio_effects)
        self.audio_library_folder = audio_library_folder
        self.output_format = output_format.lower()
        self.bitrate = bitrate
        self.export_metadata = bool(export_metadata)
        self.project_name = project_name
        self.bpm = max(40, int(bpm))
        self.temp_folder = temp_folder
        self.final_scale = final_scale

        self.video_effect_toggles = {
            "invert": True,
            "mirror": True,
            "mirror_symmetry": True,
            "low_fps": True,
            "speed_up": True,
            "speed_down": True,
            "shuffle_frames": True,
            "stutter": True,
            "random_cut_zoom": True,
            "rainbow": True,
            "frame_scramble": True,
        }
        self.audio_effect_toggles = {
            "mute": True,
            "reverse": True,
            "speed_audio": True,
            "pitch_shift": True,
            "chorus": True,
            "low_quality": True,
            "stutter_audio": True,
            "random_overlay_sound": True,
        }


class MediaScanner:
    VIDEO_EXT = set([".mp4", ".wmv", ".avi", ".mkv"])
    IMAGE_EXT = set([".png", ".jpg", ".jpeg", ".webp"])
    AUDIO_EXT = set([".mp3", ".wav", ".ogg"])

    def __init__(self, source_folder):
        self.source_folder = source_folder

    def scan(self):
        media = {
            "video_sources": [],
            "image_sources": [],
            "audio_sources": [],
        }
        if not os.path.isdir(self.source_folder):
            print("[WARN] Source folder not found: %s" % self.source_folder)
            return media

        for root, _, files in os.walk(self.source_folder):
            for file_name in files:
                full_path = os.path.join(root, file_name)
                ext = os.path.splitext(file_name)[1].lower()
                if ext in self.VIDEO_EXT:
                    media["video_sources"].append(full_path)
                elif ext in self.IMAGE_EXT:
                    media["image_sources"].append(full_path)
                elif ext in self.AUDIO_EXT:
                    media["audio_sources"].append(full_path)

        print(
            "[INFO] Media scan complete: videos=%d, images=%d, audio=%d"
            % (
                len(media["video_sources"]),
                len(media["image_sources"]),
                len(media["audio_sources"]),
            )
        )
        return media


class EffectMapper:
    def __init__(self, config):
        self.config = config
        self.effects_applied = []

    def _record(self, effect_name):
        self.effects_applied.append(effect_name)

    def enabled_effect_names(self):
        return [
            k for k, v in self.config.video_effect_toggles.items() if bool(v)
        ]

    def apply_random_effect(self, clip):
        effect_names = self.enabled_effect_names()
        if not effect_names:
            return clip
        effect_name = random.choice(effect_names)
        try:
            if effect_name == "invert":
                clip = clip.fx(vfx.invert_colors)
            elif effect_name == "mirror":
                clip = clip.fx(vfx.mirror_x)
            elif effect_name == "mirror_symmetry":
                clip = self._mirror_symmetry(clip)
            elif effect_name == "low_fps":
                clip = clip.set_fps(10)
            elif effect_name == "speed_up":
                clip = clip.fx(vfx.speedx, random.uniform(1.5, 2.5))
            elif effect_name == "speed_down":
                clip = clip.fx(vfx.speedx, random.uniform(0.4, 0.8))
            elif effect_name == "shuffle_frames":
                clip = self._shuffle_frames(clip)
            elif effect_name == "stutter":
                clip = self._stutter(clip)
            elif effect_name == "random_cut_zoom":
                clip = self._random_cut_zoom(clip)
            elif effect_name == "rainbow":
                clip = self._rainbow(clip)
            elif effect_name == "frame_scramble":
                clip = self._frame_scramble(clip)
            self._record(effect_name)
        except Exception:
            print("[WARN] Video effect failed: %s" % effect_name)
            traceback.print_exc()
        return clip

    def _mirror_symmetry(self, clip):
        mirrored = clip.fx(vfx.mirror_x)
        left = clip.resize(width=max(1, int(clip.w / 2))).set_position((0, 0))
        right = mirrored.resize(width=max(1, int(clip.w / 2))).set_position(
            (max(1, int(clip.w / 2)), 0)
        )
        return CompositeVideoClip([left, right], size=(clip.w, clip.h)).set_duration(
            clip.duration
        )

    def _shuffle_frames(self, clip):
        duration = clip.duration or 0
        if duration <= 0.15:
            return clip
        step = min(0.08, duration / 5.0)
        times = []
        t = 0.0
        while t < duration:
            times.append(t)
            t += step
        random.shuffle(times)

        def make_frame(tt):
            idx = int(min(len(times) - 1, max(0, tt / step)))
            return clip.get_frame(times[idx])

        return clip.set_make_frame(make_frame).set_duration(duration)

    def _stutter(self, clip):
        if not clip.duration or clip.duration < 0.35:
            return clip
        seg_len = random.uniform(0.1, min(0.3, clip.duration / 2.0))
        start = random.uniform(0.0, max(0.0, clip.duration - seg_len))
        segment = clip.subclip(start, start + seg_len)
        repeats = random.randint(2, 5)
        seq = [segment] * repeats
        stuttered = concatenate_videoclips(seq, method="compose")
        if stuttered.duration < clip.duration:
            tail_start = min(clip.duration, start + seg_len)
            if clip.duration - tail_start > 0.05:
                stuttered = concatenate_videoclips(
                    [stuttered, clip.subclip(tail_start, clip.duration)],
                    method="compose",
                )
        return stuttered.subclip(0, min(stuttered.duration, clip.duration))

    def _random_cut_zoom(self, clip):
        w = clip.w
        h = clip.h
        if w < 16 or h < 16:
            return clip
        zoom = random.uniform(1.1, 1.6)
        crop_w = int(w / zoom)
        crop_h = int(h / zoom)
        x1 = random.randint(0, max(0, w - crop_w))
        y1 = random.randint(0, max(0, h - crop_h))
        cropped = clip.crop(x1=x1, y1=y1, x2=x1 + crop_w, y2=y1 + crop_h)
        return cropped.resize((w, h))

    def _rainbow(self, clip):
        c1 = clip.fx(vfx.colorx, random.uniform(0.8, 1.5))
        c2 = c1.fx(vfx.lum_contrast, lum=random.randint(-20, 20), contrast=random.randint(10, 40))
        return c2

    def _frame_scramble(self, clip):
        duration = clip.duration or 0
        if duration <= 0.4:
            return clip
        parts = random.randint(3, 7)
        span = duration / float(parts)
        subclips = []
        for i in range(parts):
            a = i * span
            b = min(duration, (i + 1) * span)
            if b - a > 0.03:
                subclips.append(clip.subclip(a, b))
        if not subclips:
            return clip
        random.shuffle(subclips)
        scrambled = concatenate_videoclips(subclips, method="compose")
        return scrambled.set_duration(min(scrambled.duration, duration))


class AudioProcessor:
    def __init__(self, config):
        self.config = config
        self.effects_applied = []

    def _record(self, name):
        self.effects_applied.append(name)

    def enabled_effect_names(self):
        return [
            k for k, v in self.config.audio_effect_toggles.items() if bool(v)
        ]

    def apply_random_audio_effect(self, clip, media, temp_dir):
        if not clip or not clip.audio:
            return clip
        names = self.enabled_effect_names()
        if not names:
            return clip
        effect = random.choice(names)
        try:
            if effect == "mute":
                clip = clip.without_audio()
            elif effect == "reverse":
                clip = self._ffmpeg_audio_filter(clip, "areverse", temp_dir)
            elif effect == "speed_audio":
                rate = random.uniform(0.7, 1.4)
                clip = clip.set_audio(clip.audio.fx(vfx.speedx, rate))
            elif effect == "pitch_shift":
                semitones = random.randint(-4, 5)
                factor = math.pow(2.0, semitones / 12.0)
                filt = "asetrate=44100*%.6f,atempo=%.6f" % (factor, 1.0 / factor)
                clip = self._ffmpeg_audio_filter(clip, filt, temp_dir)
            elif effect == "chorus":
                clip = self._ffmpeg_audio_filter(
                    clip,
                    "aecho=0.8:0.9:40|80:0.4|0.3",
                    temp_dir,
                )
            elif effect == "low_quality":
                clip = self._ffmpeg_audio_filter(clip, "aresample=11025", temp_dir)
            elif effect == "stutter_audio":
                clip = self._audio_stutter(clip)
            elif effect == "random_overlay_sound":
                clip = self._overlay_random_sound(clip, media)
            self._record(effect)
        except Exception:
            print("[WARN] Audio effect failed: %s" % effect)
            traceback.print_exc()
        return clip

    def _audio_stutter(self, clip):
        if not clip.audio or clip.duration < 0.3:
            return clip
        seg = min(0.2, clip.duration / 2.0)
        start = random.uniform(0.0, max(0.0, clip.duration - seg))
        piece = clip.audio.subclip(start, start + seg)
        rep = random.randint(3, 6)
        stitched = [piece] * rep
        st = concatenate_videoclips([], method="compose") if False else None
        st_audio = stitched[0]
        for i in range(1, len(stitched)):
            st_audio = CompositeAudioClip([
                st_audio.set_start(0),
                stitched[i].set_start(i * seg),
            ]).set_duration((i + 1) * seg)
        return clip.set_audio(st_audio.set_duration(clip.duration))

    def _overlay_random_sound(self, clip, media):
        audio_pool = list(media.get("audio_sources", []))
        lib = self.config.audio_library_folder
        if lib and os.path.isdir(lib):
            for root, _, files in os.walk(lib):
                for fn in files:
                    ext = os.path.splitext(fn)[1].lower()
                    if ext in [".mp3", ".wav", ".ogg"]:
                        audio_pool.append(os.path.join(root, fn))
        if not audio_pool:
            return clip
        snd = random.choice(audio_pool)
        try:
            extra = AudioFileClip(snd)
            dur = min(clip.duration, max(0.05, extra.duration))
            extra = extra.subclip(0, dur).volumex(random.uniform(0.2, 0.8))
            if clip.audio:
                mixed = CompositeAudioClip([clip.audio, extra])
            else:
                mixed = extra
            return clip.set_audio(mixed.set_duration(clip.duration))
        except Exception:
            print("[WARN] Failed random overlay sound: %s" % snd)
            traceback.print_exc()
            return clip

    def _ffmpeg_audio_filter(self, clip, filter_chain, temp_dir):
        ffmpeg_bin = shutil.which("ffmpeg") or "ffmpeg"
        ffprobe_bin = shutil.which("ffprobe") or "ffprobe"

        in_path = os.path.join(temp_dir, "tmp_in_%d.mp4" % random.randint(1000, 999999))
        out_path = os.path.join(temp_dir, "tmp_out_%d.mp4" % random.randint(1000, 999999))
        clip.write_videofile(
            in_path,
            codec="libx264",
            audio_codec="aac",
            fps=max(10, int(clip.fps or 24)),
            verbose=False,
            logger=None,
        )

        cmd = [
            ffmpeg_bin,
            "-y",
            "-i",
            in_path,
            "-af",
            filter_chain,
            "-c:v",
            "copy",
            "-c:a",
            "aac",
            out_path,
        ]
        subprocess.run(cmd, check=True)
        _ = ffprobe_bin
        new_clip = VideoFileClip(out_path)
        return new_clip.subclip(0, min(clip.duration, new_clip.duration))


class ClipGenerator:
    def __init__(self, config, effect_mapper, audio_processor):
        self.config = config
        self.effect_mapper = effect_mapper
        self.audio_processor = audio_processor
        self.assets_used = []

    def generate_clips(self, media, temp_dir):
        mode = self.config.mode
        if mode == "YTPMV":
            return self._generate_ytpmv(media, temp_dir)
        if mode == "TENNIS":
            return self._generate_tennis(media, temp_dir)
        if mode == "COLLAB":
            return self._generate_collab(media, temp_dir)
        return self._generate_standard(media, temp_dir)

    def _base_target_duration(self):
        return random.uniform(self.config.min_duration, self.config.max_duration)

    def _safe_video_subclip(self, src, start, dur):
        try:
            v = VideoFileClip(src)
            if not v.duration or v.duration <= 0:
                v.close()
                return None
            start = min(max(0.0, start), max(0.0, v.duration - 0.05))
            end = min(v.duration, start + max(0.05, dur))
            if end - start <= 0.03:
                v.close()
                return None
            return v.subclip(start, end)
        except Exception:
            print("[WARN] Corrupt or unsupported video: %s" % src)
            traceback.print_exc()
            return None

    def _image_to_clip(self, src, duration):
        try:
            return ImageClip(src).set_duration(max(0.1, duration))
        except Exception:
            print("[WARN] Corrupt image: %s" % src)
            traceback.print_exc()
            return None

    def _pick_source_clip(self, media, force_short=False):
        videos = media.get("video_sources", [])
        images = media.get("image_sources", [])

        use_image = bool(images) and (not videos or random.random() < 0.2)
        target_dur = self._base_target_duration()
        if force_short:
            target_dur = random.uniform(self.config.min_duration, min(1.2, self.config.max_duration))

        if use_image:
            img = random.choice(images)
            clip = self._image_to_clip(img, target_dur)
            if clip:
                self.assets_used.append(img)
            return clip

        if videos:
            src = random.choice(videos)
            try:
                probe = VideoFileClip(src)
                vdur = probe.duration or 0
                probe.close()
                if vdur <= 0.1:
                    return None
                dur = min(target_dur, max(0.1, vdur - 0.01))
                start = random.uniform(0.0, max(0.0, vdur - dur))
                clip = self._safe_video_subclip(src, start, dur)
                if clip:
                    self.assets_used.append(src)
                return clip
            except Exception:
                print("[WARN] Failed to read video: %s" % src)
                traceback.print_exc()
                return None
        return None

    def _post_process_clip(self, clip, media, temp_dir, stronger_fx=False):
        if clip is None:
            return None
        try:
            if self.config.enable_video_effects:
                iterations = 2 if stronger_fx else 1
                for _ in range(iterations):
                    if random.random() < (0.75 if stronger_fx else 0.55):
                        clip = self.effect_mapper.apply_random_effect(clip)
            if self.config.enable_audio_effects and random.random() < 0.6:
                clip = self.audio_processor.apply_random_audio_effect(clip, media, temp_dir)
            return clip
        except Exception:
            print("[WARN] Post-process failed")
            traceback.print_exc()
            return clip

    def _generate_standard(self, media, temp_dir):
        clips = []
        attempts = 0
        max_attempts = self.config.clip_count * 8
        while len(clips) < self.config.clip_count and attempts < max_attempts:
            attempts += 1
            clip = self._pick_source_clip(media)
            if clip is None:
                continue
            clip = self._post_process_clip(clip, media, temp_dir)
            if clip and clip.duration and clip.duration > 0.03:
                clips.append(clip)
            else:
                try:
                    clip.close()
                except Exception:
                    pass
        return clips

    def _generate_ytpmv(self, media, temp_dir):
        clips = []
        beat = 60.0 / float(self.config.bpm)
        target = self.config.clip_count
        music = None
        if media.get("audio_sources"):
            music_file = random.choice(media["audio_sources"])
            try:
                music = AudioFileClip(music_file)
                self.assets_used.append(music_file)
            except Exception:
                music = None
        for _ in range(target):
            clip = self._pick_source_clip(media, force_short=True)
            if clip is None:
                continue
            dur = random.choice([beat / 2.0, beat, beat * 1.5])
            dur = max(self.config.min_duration, min(self.config.max_duration, dur))
            clip = clip.subclip(0, min(clip.duration, dur))
            clip = self._post_process_clip(clip, media, temp_dir, stronger_fx=True)
            if music and clip.duration > 0.03:
                t = random.uniform(0.0, max(0.0, music.duration - clip.duration))
                clip = clip.set_audio(music.subclip(t, t + clip.duration))
            clips.append(clip)
        return clips

    def _title_card(self, text, duration, resolution):
        w, h = self._parse_resolution(resolution)
        card = ColorClip((w, h), color=(0, 0, 0)).set_duration(duration)
        return card

    def _parse_resolution(self, res):
        try:
            p = res.lower().split("x")
            return int(p[0]), int(p[1])
        except Exception:
            return 1280, 720

    def _generate_tennis(self, media, temp_dir):
        clips = []
        rounds = 4
        per_round = max(1, int(self.config.clip_count / rounds))
        for r in range(rounds):
            if r > 0:
                clips.append(self._title_card("ROUND %d" % (r + 1), 0.6, self.config.resolution))
            for _ in range(per_round):
                clip = self._pick_source_clip(media, force_short=True)
                if clip is None:
                    continue
                clip = self._post_process_clip(
                    clip,
                    media,
                    temp_dir,
                    stronger_fx=(r % 2 == 1),
                )
                if clip and clip.duration > 0.03:
                    clips.append(clip)
        return clips

    def _generate_collab(self, media, temp_dir):
        clips = []
        total_target = random.uniform(20.0, 40.0)
        total = 0.0
        attempts = 0
        while total < total_target and attempts < self.config.clip_count * 12:
            attempts += 1
            clip = self._pick_source_clip(media, force_short=True)
            if clip is None:
                continue
            clip = self._post_process_clip(clip, media, temp_dir, stronger_fx=True)
            if clip and clip.duration > 0.03:
                clips.append(clip)
                total += clip.duration
        return clips


class Renderer:
    def __init__(self, config):
        self.config = config

    def render(self, clips, temp_dir):
        if not clips:
            raise RuntimeError("No clips to render")

        res = self._parse_resolution(self.config.resolution)
        normalized = []
        for c in clips:
            try:
                nc = c.resize(newsize=res)
                normalized.append(nc)
            except Exception:
                normalized.append(c)

        final = concatenate_videoclips(normalized, method="compose")
        master = os.path.join(temp_dir, "master.mp4")
        print("[INFO] Writing master file: %s" % master)
        final.write_videofile(
            master,
            codec="libx264",
            audio_codec="aac",
            bitrate=self.config.bitrate,
            fps=max(10, int(final.fps or 24)),
        )

        out_file = self._normalize_output_path()
        self._ffmpeg_finalize(master, out_file)

        for c in clips:
            try:
                c.close()
            except Exception:
                pass
        try:
            final.close()
        except Exception:
            pass

        return out_file

    def _parse_resolution(self, text):
        try:
            x, y = text.lower().split("x")
            return int(x), int(y)
        except Exception:
            return 1280, 720

    def _normalize_output_path(self):
        base, ext = os.path.splitext(self.config.output_file)
        expected = ".%s" % self.config.output_format
        if ext.lower() != expected:
            return base + expected
        return self.config.output_file

    def _ffmpeg_finalize(self, in_file, out_file):
        ffmpeg_bin = shutil.which("ffmpeg") or "ffmpeg"
        cmd = [
            ffmpeg_bin,
            "-y",
            "-i",
            in_file,
            "-c:v",
            "libx264",
            "-b:v",
            self.config.bitrate,
            "-af",
            "loudnorm",
        ]

        if self.config.final_scale:
            cmd.extend(["-vf", "scale=%s" % self.config.final_scale])

        if self.config.output_format in ["wmv"]:
            cmd[cmd.index("libx264")] = "wmv2"
        elif self.config.output_format in ["avi"]:
            cmd[cmd.index("libx264")] = "mpeg4"
        elif self.config.output_format in ["mkv", "mp4"]:
            pass

        cmd.append(out_file)

        print("[INFO] FFmpeg command: %s" % " ".join(cmd))
        subprocess.run(cmd, check=True)


class MetadataExporter:
    def __init__(self, config):
        self.config = config

    def export(self, output_file, assets_used, effects_applied, clip_count):
        metadata = {
            "ProjectName": self.config.project_name,
            "Mode": self.config.mode,
            "AssetsUsed": self._uniq(assets_used),
            "EffectsApplied": self._uniq(effects_applied),
            "OutputFile": output_file,
            "ClipCount": int(clip_count),
            "MinDuration": float(self.config.min_duration),
            "MaxDuration": float(self.config.max_duration),
            "AutoKeyframeData": self._auto_keyframe_data(clip_count),
        }
        json_path = os.path.splitext(output_file)[0] + ".ytpproj.json"
        with open(json_path, "w") as f:
            json.dump(metadata, f, indent=2)
        print("[INFO] Metadata exported: %s" % json_path)
        return json_path

    def _auto_keyframe_data(self, clip_count):
        data = []
        time_cursor = 0.0
        for _ in range(max(4, int(clip_count / 2))):
            time_cursor += random.uniform(0.2, 1.3)
            data.append(
                {
                    "time": round(time_cursor, 3),
                    "effect": random.choice(["zoom", "shake", "flash", "rotate"]),
                    "value": round(random.uniform(0.2, 1.8), 3),
                }
            )
        return data

    def _uniq(self, items):
        seen = set()
        out = []
        for item in items:
            if item not in seen:
                seen.add(item)
                out.append(item)
        return out


def check_ffmpeg_available():
    ff = shutil.which("ffmpeg")
    if ff:
        return ff
    local_ff = os.path.join(os.getcwd(), "ffmpeg.exe")
    if os.path.isfile(local_ff):
        return local_ff
    raise RuntimeError("FFmpeg not found in PATH or current folder")


def parse_args(argv):
    parser = argparse.ArgumentParser(description="YTPGen Mega Python Generator Backend")
    parser.add_argument("--source", required=True, help="Source media folder")
    parser.add_argument("--output", required=True, help="Output video file")
    parser.add_argument("--mode", default="STANDARD", choices=["STANDARD", "YTPMV", "TENNIS", "COLLAB"])
    parser.add_argument("--clip-count", type=int, default=20)
    parser.add_argument("--min-duration", type=float, default=0.5)
    parser.add_argument("--max-duration", type=float, default=2.5)
    parser.add_argument("--resolution", default="1280x720")
    parser.add_argument("--no-video-effects", action="store_true")
    parser.add_argument("--no-audio-effects", action="store_true")
    parser.add_argument("--audio-library", default="")
    parser.add_argument("--format", default="mp4", choices=["mp4", "wmv", "avi", "mkv"])
    parser.add_argument("--bitrate", default="2500k")
    parser.add_argument("--export-metadata", action="store_true")
    parser.add_argument("--project-name", default="YTPGen Mega Project")
    parser.add_argument("--bpm", type=int, default=120)
    parser.add_argument("--temp-folder", default="")
    parser.add_argument("--scale", default="")
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv or sys.argv[1:])

    config = GeneratorConfig(
        source_folder=args.source,
        output_file=args.output,
        mode=args.mode,
        clip_count=args.clip_count,
        min_duration=args.min_duration,
        max_duration=args.max_duration,
        resolution=args.resolution,
        enable_video_effects=not args.no_video_effects,
        enable_audio_effects=not args.no_audio_effects,
        audio_library_folder=args.audio_library,
        output_format=args.format,
        bitrate=args.bitrate,
        export_metadata=args.export_metadata,
        project_name=args.project_name,
        bpm=args.bpm,
        temp_folder=args.temp_folder,
        final_scale=args.scale,
    )

    try:
        ffmpeg_loc = check_ffmpeg_available()
        print("[INFO] FFmpeg found: %s" % ffmpeg_loc)
    except Exception as e:
        print("[ERROR] %s" % str(e))
        return 2

    scanner = MediaScanner(config.source_folder)
    media = scanner.scan()

    if not media["video_sources"] and not media["image_sources"]:
        print("[ERROR] No video/image sources found.")
        return 3

    tmp_base = config.temp_folder if config.temp_folder else None
    temp_dir = tempfile.mkdtemp(prefix="ytpgen_", dir=tmp_base)
    print("[INFO] Temporary dir: %s" % temp_dir)

    try:
        effect_mapper = EffectMapper(config)
        audio_processor = AudioProcessor(config)
        generator = ClipGenerator(config, effect_mapper, audio_processor)
        renderer = Renderer(config)
        metadata = MetadataExporter(config)

        clips = generator.generate_clips(media, temp_dir)
        if not clips:
            print("[ERROR] Failed to generate clips.")
            return 4

        output = renderer.render(clips, temp_dir)
        print("[INFO] Render complete: %s" % output)

        if config.export_metadata:
            metadata.export(
                output,
                generator.assets_used,
                effect_mapper.effects_applied + audio_processor.effects_applied,
                len(clips),
            )

    except subprocess.CalledProcessError as e:
        print("[ERROR] External command failed: %s" % str(e))
        return 5
    except Exception:
        print("[ERROR] Unhandled exception in generation pipeline")
        traceback.print_exc()
        return 6
    finally:
        try:
            shutil.rmtree(temp_dir, ignore_errors=True)
        except Exception:
            pass

    return 0


if __name__ == "__main__":
    sys.exit(main())
