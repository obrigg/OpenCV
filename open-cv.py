import cv2
import glob
import os

def images_to_video(video_file: str, image_directory: str, image_type: str, fps: int):
    image_list = glob.glob(f"{image_directory}/*.{image_type}")
    sorted_images = sorted(image_list, key=os.path.getmtime)
    height, width, channels = cv2.imread(image_list[0]).shape
    print(f"About to transform the following image list: {sorted_images}\
        \nInto a {width}x{height} video with {fps} FPS")
    out = cv2.VideoWriter(video_file, cv2.VideoWriter_fourcc(*'mp4v'), fps, (width,height))
    for file in image_list:
        image_frame  = cv2.imread(file)
        out.write(image_frame)
    out.release()


if __name__ == "__main__":
    video_file = "output.mp4"
    image_directory = "images"
    fps = 5
    image_type = "png"

    images_to_video(video_file, image_directory, image_type, fps)