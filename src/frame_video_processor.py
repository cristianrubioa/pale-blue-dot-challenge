import os

import cv2

from src.settings import settings

input_directory = os.path.join(
    settings.IMAGES_DATASET.DATASET_PATH,
    settings.IMAGES_DATASET.FRAME_VISUALIZATION_DATASET_PATH,
)

output_directory_file = os.path.join(
    settings.IMAGES_DATASET.DATASET_PATH,
    settings.IMAGES_DATASET.FRAME_VIDEO_DATASET_PATH,
    settings.IMAGES_DATASET.FRAME_VIDEO_FILE,
)


def create_video(input_dir, output_path, frame_rate):
    # Get the list of PNG files in the input directory
    files = sorted([f for f in os.listdir(input_dir) if f.endswith(".png")])

    if not files:
        print("No PNG files found in the specified directory.")
        return

    # Get the first image to determine the size of the video
    first_image_path = os.path.join(input_dir, files[0])
    first_image = cv2.imread(first_image_path)
    height, width, _ = first_image.shape

    # Define the codec and create VideoWriter object
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")  # You can change the codec as needed
    video_writer = cv2.VideoWriter(output_path, fourcc, frame_rate, (width, height))

    # Write each frame to the video
    for file in files:
        image_path = os.path.join(input_dir, file)
        frame = cv2.imread(image_path)
        video_writer.write(frame)

    # Release the VideoWriter object
    video_writer.release()

    print(f"Video created successfully at: {output_path}")


create_video(input_directory, output_directory_file, 2)
