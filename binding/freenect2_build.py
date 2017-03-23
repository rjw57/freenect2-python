import codecs
import os
import subprocess
from cffi import FFI

this_dir = os.path.abspath(os.path.dirname(__file__))

with open(os.path.join(this_dir, 'freenect2-c.cpp')) as fobj:
    binding_source = fobj.read()

extra_compile_args = codecs.decode(subprocess.check_output(
    'pkg-config freenect2 --cflags'.split()), 'ascii').split()
extra_link_args = codecs.decode(subprocess.check_output(
    'pkg-config freenect2 --libs'.split()), 'ascii').split()

ffibuilder = FFI()

ffibuilder.set_source(
    "freenect2._freenect2", binding_source,
    libraries=['freenect2'], source_extension='.cpp',
    extra_compile_args=extra_compile_args,
    extra_link_args=extra_link_args)

ffibuilder.cdef(r'''
typedef enum {
    FRAME_TYPE_COLOR, FRAME_TYPE_IR, FRAME_TYPE_DEPTH, ...
} Freenect2FrameType;

typedef enum {
    FRAME_FORMAT_INVALID, FRAME_FORMAT_RAW, FRAME_FORMAT_FLOAT,
    FRAME_FORMAT_BGRX, FRAME_FORMAT_RGBX, FRAME_FORMAT_GRAY, ...
} Freenect2FrameFormat;

typedef void *Freenect2Ref;
typedef void *Freenect2DeviceRef;
typedef void *Freenect2FrameRef;
typedef void *Freenect2FrameListenerRef;
typedef void *Freenect2RegistrationRef;

typedef struct {
    float fx, fy, cx, cy, k1, k2, k3, p1, p2;
    ...;
} IrCameraParams;

typedef struct {
    float fx, fy, cx, cy;
    float shift_d, shift_m;
    float mx_x3y0; // xxx
    float mx_x0y3; // yyy
    float mx_x2y1; // xxy
    float mx_x1y2; // yyx
    float mx_x2y0; // xx
    float mx_x0y2; // yy
    float mx_x1y1; // xy
    float mx_x1y0; // x
    float mx_x0y1; // y
    float mx_x0y0; // 1

    float my_x3y0; // xxx
    float my_x0y3; // yyy
    float my_x2y1; // xxy
    float my_x1y2; // yyx
    float my_x2y0; // xx
    float my_x0y2; // yy
    float my_x1y1; // xy
    float my_x1y0; // x
    float my_x0y1; // y
    float my_x0y0; // 1
    ...;
} ColorCameraParams;

Freenect2Ref freenect2_create(void);
void freenect2_dispose(Freenect2Ref fn2_ref);
int freenect2_enumerate_devices(Freenect2Ref fn2_ref);

Freenect2DeviceRef freenect2_open_default_device(Freenect2Ref fn2_ref);
Freenect2DeviceRef freenect2_open_device_by_index(
    Freenect2Ref fn2_ref, int index);
Freenect2DeviceRef freenect2_open_device_by_serial(
    Freenect2Ref fn2_ref, const char* serial);

int freenect2_device_start(Freenect2DeviceRef device_ref);
int freenect2_device_stop(Freenect2DeviceRef device_ref);
int freenect2_device_close(Freenect2DeviceRef device_ref);
void freenect2_device_set_color_frame_listener(
    Freenect2DeviceRef device_ref, Freenect2FrameListenerRef fl_ref);
void freenect2_device_set_ir_and_depth_frame_listener(
    Freenect2DeviceRef device_ref, Freenect2FrameListenerRef fl_ref);
IrCameraParams freenect2_device_get_ir_camera_params(
    Freenect2DeviceRef device_ref);
ColorCameraParams freenect2_device_get_color_camera_params(
    Freenect2DeviceRef device_ref);

typedef int (*Freenect2FrameListenerFunc) (
    Freenect2FrameType type, Freenect2FrameRef frame, void *user_data);
Freenect2FrameListenerRef freenect2_frame_listener_create(
    Freenect2FrameListenerFunc func, void* user_data);
void freenect2_frame_listener_dispose(Freenect2FrameListenerRef fl_ref);

extern "Python" int frame_listener_callback(
    Freenect2FrameType type, Freenect2FrameRef frame, void *user_data);

Freenect2FrameRef freenect2_frame_create(
    size_t width, size_t height, size_t bytes_per_pixel);
void freenect2_frame_dispose(Freenect2FrameRef frame_ref);

size_t freenect2_frame_get_width(Freenect2FrameRef frame_ref);
size_t freenect2_frame_get_height(Freenect2FrameRef frame_ref);
size_t freenect2_frame_get_bytes_per_pixel(Freenect2FrameRef frame_ref);
void* freenect2_frame_get_data(Freenect2FrameRef frame_ref);
uint32_t freenect2_frame_get_timestamp(Freenect2FrameRef frame_ref);
uint32_t freenect2_frame_get_sequence(Freenect2FrameRef frame_ref);
float freenect2_frame_get_exposure(Freenect2FrameRef frame_ref);
float freenect2_frame_get_gain(Freenect2FrameRef frame_ref);
float freenect2_frame_get_gamma(Freenect2FrameRef frame_ref);
uint32_t freenect2_frame_get_status(Freenect2FrameRef frame_ref);
Freenect2FrameFormat freenect2_frame_get_format(Freenect2FrameRef frame_ref);

void freenect2_frame_set_width(Freenect2FrameRef frame_ref, size_t value);
void freenect2_frame_set_height(Freenect2FrameRef frame_ref, size_t value);
void freenect2_frame_set_bytes_per_pixel(Freenect2FrameRef frame_ref, size_t value);
void freenect2_frame_set_timestamp(Freenect2FrameRef frame_ref, uint32_t value);
void freenect2_frame_set_sequence(Freenect2FrameRef frame_ref, uint32_t value);
void freenect2_frame_set_exposure(Freenect2FrameRef frame_ref, float value);
void freenect2_frame_set_gain(Freenect2FrameRef frame_ref, float value);
void freenect2_frame_set_gamma(Freenect2FrameRef frame_ref, float value);
void freenect2_frame_set_status(Freenect2FrameRef frame_ref, uint32_t value);
void freenect2_frame_set_format(Freenect2FrameRef frame_ref, Freenect2FrameFormat value);

Freenect2RegistrationRef freenect2_registration_create(
    IrCameraParams depth_p, ColorCameraParams rgb_p);
void freenect2_registration_dispose(Freenect2RegistrationRef reg_ref);
void freenect2_registration_apply(
    Freenect2RegistrationRef reg_ref, Freenect2FrameRef rgb_ref,
    Freenect2FrameRef depth_ref, Freenect2FrameRef undistorted_ref,
    Freenect2FrameRef registered_ref, int enable_filter,
    Freenect2FrameRef big_depth_ref);
void freenect2_registration_get_points_xyz(
    Freenect2RegistrationRef reg_ref, Freenect2FrameRef undistorted_ref,
    const int32_t* rows, const int32_t* cols, size_t n_points,
    float* out_xs, float* out_ys, float* out_zs);
''')

if __name__ == "__main__":
    ffibuilder.compile(verbose=True)
