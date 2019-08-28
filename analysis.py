from datetime import datetime
import os
import re

import numpy
import PIL
from PIL import Image
import matplotlib.pyplot as plt

def clear_edited_files():
  for filename in os.listdir("./photos_edited"):
    os.remove("./photos_edited/" + filename)

def clear_thresholded_files():
  for filename in os.listdir("./photos_threshold"):
    os.remove("./photos_threshold/" + filename)

def get_list_of_filenames():
  filenames = os.listdir("./photos")
  filenames = sorted(filenames)

  chosen_filenames = []

  for filename in filenames:
    match = re.match(".*--(\d{2})-00", filename)
    if (match is None):
      continue
    hour = match.groups()[0]
    hour = int(hour)
    if ((hour - 1) % 2 == 0 and hour >= 6 and hour <= 20):
      chosen_filenames.append(filename)

  return chosen_filenames

def modify_image(src_filename, dest_filename):
  image = Image.open(src_filename)

  # crop
  top = 80
  bottom = 2464 - ((154 * 2) - top)
  right = 3280 - (205 * 2)
  image = image.crop((0, top, right, bottom))

  # resize
  maxsize = (820, 616)  # 4 times smaller than 3280, 2464
  image.thumbnail(maxsize, PIL.Image.ANTIALIAS)

  image.save(dest_filename, "JPEG")

def pixelThresholdRed(intensity):
  return 255 if intensity > 110 else 0

def pixelThresholdGreen(intensity):
  return 255 # if intensity > 110 else 0

def pixelThresholdBlue(intensity):
  return 255 # if intensity > 70 else 0

def threshold_image(src_filename, dest_filename):
  image = Image.open(src_filename)

  left = 80
  top = 80
  right = 820 - (80 * 2)
  bottom = 616 - (80 * 2)
  image = image.crop((left, top, right, bottom))

  multiBands = image.split()
  redBand   = multiBands[0].point(pixelThresholdRed)
  greenBand = multiBands[1].point(pixelThresholdGreen)
  blueBand  = multiBands[2].point(pixelThresholdBlue)
  newImage = Image.merge("RGB", (redBand, greenBand, blueBand))
  newImage.save(dest_filename, "JPEG")

def modify_files(filenames):
  for filename in filenames:
    print("modifying: " + filename)

    src_filename = "./photos/" + filename
    dest_filename = "./photos_edited/" + filename
    modify_image(src_filename, dest_filename)

    src_filename = dest_filename
    dest_filename = "./photos_threshold/" + filename
    threshold_image(src_filename, dest_filename)

def get_growth_data(assume_3d, drop_indexes=set()):
  x = []
  y = []

  for (index, filename) in enumerate(sorted(os.listdir("./photos_threshold"))[0:]):
    if index in drop_indexes:
      continue
    timestamp = datetime.strptime(filename, "%Y-%m-%d--%H-%M-%S.jpg").timestamp()
    x.append(round(timestamp / 3600))

    image = Image.open("./photos_threshold/" + filename)
    # Get the red channel data
    red_channel_data = image.split()[0].getdata()
    y.append(sum(red_channel_data))

  min_x = min(x)
  x = [v - min_x for v in x]

  max_y = max(y)
  y = [1 + max_y - v for v in y]
  if assume_3d:
    # assuming that we are measuring in 2 dimensions and biology is growing in 3 dimensions
    y = [v ** 1.5 for v in y]

  return { "x": x, "y": y }

def calculate_fit(growth_data):
  x = growth_data["x"]
  y = growth_data["y"]
  return numpy.polyfit(x, numpy.log(y), 1, w=numpy.sqrt(y))

def plot_graph(growth_data, fit, dimension):
  x = growth_data["x"]
  y = growth_data["y"]
  fitted_y = numpy.exp(fit[1]) * numpy.exp(fit[0] * numpy.array(x))

  plt.plot(x, y, marker="o", linestyle="--", color="r", label="Nature")
  plt.plot(x, fitted_y, marker="o", linestyle="--", color="b", label=dimension + " Fit")
  plt.xlabel("hours from start")
  plt.ylabel("inverse red channel")
  plt.title("Nature's exponential growth")
  plt.legend()
  plt.show()

def main():
  clear_edited_files()
  clear_thresholded_files()
  filenames = get_list_of_filenames()
  modify_files(filenames)

  drop_indexes = set([3, 9])
  growth_data_2d = get_growth_data(assume_3d=False, drop_indexes=drop_indexes)
  growth_data_3d = get_growth_data(assume_3d=True, drop_indexes=drop_indexes)
  fit_2d = calculate_fit(growth_data_2d)
  fit_3d = calculate_fit(growth_data_3d)
  plot_graph(growth_data_2d, fit_2d, "2d")
  plot_graph(growth_data_3d, fit_3d, "3d")

main()

print("""You might now want to run:
convert -monitor -delay 20 -loop 0 photos_edited/*jpg animated.gif
convert -monitor -delay 20 -loop 0 photos_threshold/*jpg animated_threshold.gif
convert -monitor animated.gif -resize 274x205 animated_small.gif
""")
