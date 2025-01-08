import os
import csv
from moviepy.editor import VideoFileClip


def capture_screenshots(video_folder: str, screenshot_folder: str, output_csv: str, interval: int) -> None:
    os.makedirs(screenshot_folder, exist_ok=True)

    with open(output_csv, mode='w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["video_path", "screenshot_path"])

        for filename in os.listdir(video_folder):
            if filename.lower().endswith(('.mp4', '.mov', '.avi', '.mkv')):
                video_path = os.path.join(video_folder, filename)
                clip = VideoFileClip(video_path)
                duration = int(clip.duration)

                for t in range(0, duration, interval):
                    screenshot_name = (f"{os.path.splitext(filename)[0]}_"
                                       f"{t}.jpg")
                    screenshot_path = os.path.join(
                        screenshot_folder,
                        screenshot_name
                    )
                    clip.save_frame(screenshot_path, t)
                    writer.writerow([video_path, screenshot_path])
                clip.close()


if __name__ == "__main__":
    video_dir = (
        r"C:\Users\Nelson Siu\OneDrive - University of Toronto\Desktop\projects\ICM_chipscraper\videos"
    )
    screenshot_dir = (
        r"C:\Users\Nelson Siu\OneDrive - University of Toronto\Desktop\projects\ICM_chipscraper\screenshots"
    )
    csv_path = "output.csv"
    capture_screenshots(video_dir, screenshot_dir, csv_path, 10)    