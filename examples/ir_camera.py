"""
Simple IR camera using freenect2. Saves captured IR image
to output.jpg.

"""
# Import parts of freenect2 we're going to use
from freenect2 import Device, FrameType

# We use numpy to process the raw IR frame
import numpy as np

# We use the Pillow library for saving the captured image
from PIL import Image

# Open default device
device = Device()

# Start the device
with device.running():
    # For each received frame...
    for type_, frame in device:
        # ...stop only when we get an IR frame
        if type_ is FrameType.Ir:
            break

# Outside of the 'with' block, the device has been stopped again

# The received IR frame is in the range 0 -> 65535. Normalise the
# range to 0 -> 1 and take square root as a simple form of gamma
# correction.
ir_image = frame.to_array()
ir_image /= ir_image.max()
ir_image = np.sqrt(ir_image)

# Use Pillow to save the IR image.
Image.fromarray(256 * ir_image).convert('L').save('output.jpg')
