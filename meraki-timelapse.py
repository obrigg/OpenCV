import cv2
import os
import requests
import time
import json
import glob
from datetime import timedelta, datetime
from rich.progress import track


# User inputs
mv_serial = "Q2FV-VYGH-ZVB3"
snapshot_frequency = 5      # in minutes
timelapse_timeframe = 24     # in hours


def take_snapshot(meraki_timestamp):
    url = f"https://api.meraki.com/api/v1/devices/{mv_serial}/camera/generateSnapshot"
    headers = {'X-Cisco-Meraki-API-Key': meraki_key, 'Content-Type': 'application/json'}
    try:        
        response = requests.post(url=url, headers=headers, data=json.dumps(meraki_timestamp))
    except:
        print(f"Failed to get a snapshot url - exception was raised")
        return("Error")
    if response.status_code == 202:
        snapshot_url = response.json()['url']
        #print(f"\nSnapshot URL: {snapshot_url}\n")
        return(snapshot_url)
    else:
        print(f"Failed to get a snapshot url. Error: {response.status_code}")
        return("Error")


def save_snapshot(snapshot_url: str, filename: str):
    try:
        snapshot = requests.get(snapshot_url)
        if snapshot.status_code == 200:
            with open(filename, 'wb') as f:
                for chunk in snapshot.iter_content(chunk_size=8192):
                    f.write(chunk)
            return("Ok")
        else:
            #print(f"\nError fetching snapshot at: {snapshot_url}\nReceived {snapshot.status_code}")
            return(snapshot.status_code)
    except:
        print(f"Error saving a snapshot: {snapshot_url}")


def images_to_video(video_file: str, image_directory: str, image_type: str, fps: int):
    image_list = glob.glob(f"{image_directory}/*.{image_type}")
    sorted_images = sorted(image_list)
    height, width, channels = cv2.imread(image_list[0]).shape
    print(f"\n\n\nAbout to transform the following image list: {sorted_images}\
        \n\ninto a {width}x{height} video with {fps} FPS")
    out = cv2.VideoWriter(video_file, cv2.VideoWriter_fourcc(*'mp4v'), fps, (width,height))
    for file in sorted_images:
        image_frame  = cv2.imread(file)
        out.write(image_frame)
    out.release()

now = datetime.utcnow()
timestamp = now-timedelta(hours=timelapse_timeframe)
number_of_snapshots = int((now-timestamp)/timedelta(minutes=snapshot_frequency))
snapshot_details = {}
meraki_key = os.environ.get('MERAKI_KEY')
sleeping_time = 1*60
if not os.path.isdir('snapshots'):
    os.mkdir('snapshots')

# Generating snapshots via Meraki's Dashboard API.
print(f"Expected results by {time.ctime(time.time() + number_of_snapshots/10*61)}")
for i in track(range(number_of_snapshots), description="Generating and saving snapshots..."):
    meraki_timestamp = {"timestamp": str(timestamp.isoformat() + "Z")}
    try:
        snapshot_url = take_snapshot(meraki_timestamp)
        snapshot_details[timestamp.isoformat()[:16].replace(":", "-")] = {"url": snapshot_url}
    except:
        print("Oops")
    timestamp += timedelta(minutes=snapshot_frequency)
    # After 10 snapshots - pause and retrieve them
    if (i+1) % 10 == 0:
        print(f"Waiting {sleeping_time} seconds")
        time.sleep(sleeping_time)
        for snapshot_name in snapshot_details:
            if not "status" in snapshot_details[snapshot_name].keys():
                snapshot_details[snapshot_name]['status'] = save_snapshot(snapshot_details[snapshot_name]["url"],f"./snapshots/{snapshot_name}.jpg")
            elif snapshot_details[snapshot_name]['status'] != "Ok":
                    snapshot_details[snapshot_name]['status'] = save_snapshot(snapshot_details[snapshot_name]["url"],f"./snapshots/{snapshot_name}.jpg")
        print(f"Waiting {sleeping_time} seconds")
        time.sleep(sleeping_time)
#
print(f"Waiting another {int(sleeping_time/60)} minutes... just in case.")
time.sleep(sleeping_time)
# Fetching and saving the photos to the local PC.
ok_counter = 0
for snapshot_name in snapshot_details:
    if not "status" in snapshot_details[snapshot_name].keys():
        snapshot_details[snapshot_name]['status'] = save_snapshot(snapshot_details[snapshot_name]["url"],f"./snapshots/{snapshot_name}.jpg")
    if snapshot_details[snapshot_name]['status'] == "Ok":
        ok_counter += 1
print(snapshot_details)
print(f"Successfully downloaded {ok_counter} out of {number_of_snapshots} photos")

# Creating a timelapse video out of the photo series.
images_to_video("meraki_timelaps.mp4", "snapshots", "jpg", 20)