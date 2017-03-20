import os
from cffi import FFI

this_dir = os.path.abspath(os.path.dirname(__file__))

ffibuilder = FFI()

ffibuilder.set_source(
    "freenect2._freenect2", r'''
#include <libfreenect2/libfreenect2.hpp>
#include <libfreenect2/registration.h>

extern "C" {

typedef void *Freenect2Ref;
typedef void *Freenect2DeviceRef;
typedef void *Freenect2FrameListenerRef;
typedef void *Freenect2FrameRef;
typedef void *Freenect2RegistrationRef;

class Freenect2FrameListener;

using namespace libfreenect2;

typedef enum {
    FRAME_TYPE_COLOR = Frame::Color,
    FRAME_TYPE_IR = Frame::Ir,
    FRAME_TYPE_DEPTH = Frame::Depth,
} Freenect2FrameType;

typedef enum {
    FRAME_FORMAT_INVALID = Frame::Invalid,
    FRAME_FORMAT_RAW = Frame::Raw,
    FRAME_FORMAT_FLOAT = Frame::Float,
    FRAME_FORMAT_BGRX = Frame::BGRX,
    FRAME_FORMAT_RGBX = Frame::RGBX,
    FRAME_FORMAT_GRAY = Frame::Gray,
} Freenect2FrameFormat;

typedef Freenect2Device::IrCameraParams IrCameraParams;
typedef Freenect2Device::ColorCameraParams ColorCameraParams;

Freenect2Ref freenect2_create(void)
{
    return reinterpret_cast<Freenect2Ref>(new Freenect2());
}

void freenect2_dispose(Freenect2Ref fn2)
{
    delete reinterpret_cast<Freenect2*>(fn2);
}

int freenect2_enumerate_devices(Freenect2Ref fn2_ref)
{
    Freenect2* fn2 = reinterpret_cast<Freenect2*>(fn2_ref);
    return fn2->enumerateDevices();
}

Freenect2DeviceRef freenect2_open_default_device(Freenect2Ref fn2_ref)
{
    Freenect2* fn2 = reinterpret_cast<Freenect2*>(fn2_ref);
    return reinterpret_cast<Freenect2DeviceRef>(fn2->openDefaultDevice());
}

Freenect2DeviceRef freenect2_open_device_by_index(Freenect2Ref fn2_ref, int index)
{
    Freenect2* fn2 = reinterpret_cast<Freenect2*>(fn2_ref);
    return reinterpret_cast<Freenect2DeviceRef>(fn2->openDevice(index));
}

Freenect2DeviceRef freenect2_open_device_by_serial(
    Freenect2Ref fn2_ref, const char* serial)
{
    Freenect2* fn2 = reinterpret_cast<Freenect2*>(fn2_ref);
    return reinterpret_cast<Freenect2DeviceRef>(
        fn2->openDevice(std::string(serial)));
}

int freenect2_device_start(Freenect2DeviceRef device_ref) {
    Freenect2Device* device = reinterpret_cast<Freenect2Device*>(device_ref);
    return device->start();
}

int freenect2_device_stop(Freenect2DeviceRef device_ref) {
    Freenect2Device* device = reinterpret_cast<Freenect2Device*>(device_ref);
    return device->stop();
}

int freenect2_device_close(Freenect2DeviceRef device_ref) {
    Freenect2Device* device = reinterpret_cast<Freenect2Device*>(device_ref);
    return device->close();
}

void freenect2_device_set_color_frame_listener(
    Freenect2DeviceRef device_ref, Freenect2FrameListenerRef fl_ref)
{
    Freenect2Device* device = reinterpret_cast<Freenect2Device*>(device_ref);
    FrameListener* fl = reinterpret_cast<FrameListener*>(fl_ref);
    device->setColorFrameListener(fl);
}

void freenect2_device_set_ir_and_depth_frame_listener(
    Freenect2DeviceRef device_ref, Freenect2FrameListenerRef fl_ref)
{
    Freenect2Device* device = reinterpret_cast<Freenect2Device*>(device_ref);
    FrameListener* fl = reinterpret_cast<FrameListener*>(fl_ref);
    device->setIrAndDepthFrameListener(fl);
}

IrCameraParams freenect2_device_get_ir_camera_params(
    Freenect2DeviceRef device_ref)
{
    Freenect2Device* device = reinterpret_cast<Freenect2Device*>(device_ref);
    return device->getIrCameraParams();
}

ColorCameraParams freenect2_device_get_color_camera_params(
    Freenect2DeviceRef device_ref)
{
    Freenect2Device* device = reinterpret_cast<Freenect2Device*>(device_ref);
    return device->getColorCameraParams();
}

typedef int (*Freenect2FrameListenerFunc) (
    Freenect2FrameType type, Freenect2FrameRef frame, void *user_data);

class Freenect2FrameListener : public FrameListener
{
public:
    Freenect2FrameListener(
        Freenect2FrameListenerFunc func,
        void* user_data=NULL)
    : func_(func), user_data_(user_data) { }

    virtual ~Freenect2FrameListener() { }

    virtual bool onNewFrame(Frame::Type type, Frame *frame)
    {
        return func_(
            static_cast<Freenect2FrameType>(type),
            reinterpret_cast<Freenect2FrameRef>(frame),
            user_data_);
    }

protected:
    Freenect2FrameListenerFunc func_;
    void *user_data_;
};

Freenect2FrameListenerRef freenect2_frame_listener_create(
    Freenect2FrameListenerFunc func, void* user_data)
{
    return reinterpret_cast<Freenect2FrameListenerRef>(
        new Freenect2FrameListener(func, user_data));
}

void freenect2_frame_listener_dispose(Freenect2FrameListenerRef fl_ref)
{
    Freenect2FrameListener* fl = reinterpret_cast<Freenect2FrameListener*>(fl_ref);
    delete fl;
}

Freenect2FrameRef freenect2_frame_create(
    size_t width, size_t height, size_t bytes_per_pixel)
{
    return reinterpret_cast<Freenect2FrameRef>(
        new Frame(width, height, bytes_per_pixel));
}

void freenect2_frame_dispose(Freenect2FrameRef frame_ref)
{
    Frame* frame = reinterpret_cast<Frame*>(frame_ref);
    delete frame;
}

size_t freenect2_frame_get_width(Freenect2FrameRef frame_ref)
{
    Frame* frame = reinterpret_cast<Frame*>(frame_ref);
    return frame->width;
}

size_t freenect2_frame_get_height(Freenect2FrameRef frame_ref)
{
    Frame* frame = reinterpret_cast<Frame*>(frame_ref);
    return frame->height;
}

size_t freenect2_frame_get_bytes_per_pixel(Freenect2FrameRef frame_ref)
{
    Frame* frame = reinterpret_cast<Frame*>(frame_ref);
    return frame->bytes_per_pixel;
}

void* freenect2_frame_get_data(Freenect2FrameRef frame_ref)
{
    Frame* frame = reinterpret_cast<Frame*>(frame_ref);
    return frame->data;
}

uint32_t freenect2_frame_get_timestamp(Freenect2FrameRef frame_ref)
{
    Frame* frame = reinterpret_cast<Frame*>(frame_ref);
    return frame->timestamp;
}

uint32_t freenect2_frame_get_sequence(Freenect2FrameRef frame_ref)
{
    Frame* frame = reinterpret_cast<Frame*>(frame_ref);
    return frame->sequence;
}

float freenect2_frame_get_exposure(Freenect2FrameRef frame_ref)
{
    Frame* frame = reinterpret_cast<Frame*>(frame_ref);
    return frame->exposure;
}

float freenect2_frame_get_gain(Freenect2FrameRef frame_ref)
{
    Frame* frame = reinterpret_cast<Frame*>(frame_ref);
    return frame->gain;
}

float freenect2_frame_get_gamma(Freenect2FrameRef frame_ref)
{
    Frame* frame = reinterpret_cast<Frame*>(frame_ref);
    return frame->gamma;
}

uint32_t freenect2_frame_get_status(Freenect2FrameRef frame_ref)
{
    Frame* frame = reinterpret_cast<Frame*>(frame_ref);
    return frame->status;
}

void freenect2_frame_set_width(Freenect2FrameRef frame_ref, size_t value)
{
    Frame* frame = reinterpret_cast<Frame*>(frame_ref);
    frame->width = value;
}

void freenect2_frame_set_height(Freenect2FrameRef frame_ref, size_t value)
{
    Frame* frame = reinterpret_cast<Frame*>(frame_ref);
    frame->height = value;
}

void freenect2_frame_set_bytes_per_pixel(Freenect2FrameRef frame_ref, size_t value)
{
    Frame* frame = reinterpret_cast<Frame*>(frame_ref);
    frame->bytes_per_pixel = value;
}

void freenect2_frame_set_timestamp(Freenect2FrameRef frame_ref, uint32_t value)
{
    Frame* frame = reinterpret_cast<Frame*>(frame_ref);
    frame->timestamp = value;
}

void freenect2_frame_set_sequence(Freenect2FrameRef frame_ref, uint32_t value)
{
    Frame* frame = reinterpret_cast<Frame*>(frame_ref);
    frame->sequence = value;
}

void freenect2_frame_set_exposure(Freenect2FrameRef frame_ref, float value)
{
    Frame* frame = reinterpret_cast<Frame*>(frame_ref);
    frame->exposure = value;
}

void freenect2_frame_set_gain(Freenect2FrameRef frame_ref, float value)
{
    Frame* frame = reinterpret_cast<Frame*>(frame_ref);
    frame->gain = value;
}

void freenect2_frame_set_gamma(Freenect2FrameRef frame_ref, float value)
{
    Frame* frame = reinterpret_cast<Frame*>(frame_ref);
    frame->gamma = value;
}

void freenect2_frame_set_status(Freenect2FrameRef frame_ref, uint32_t value)
{
    Frame* frame = reinterpret_cast<Frame*>(frame_ref);
    frame->status = value;
}

void freenect2_frame_set_format(Freenect2FrameRef frame_ref, Freenect2FrameFormat value)
{
    Frame* frame = reinterpret_cast<Frame*>(frame_ref);
    frame->format = static_cast<Frame::Format>(value);
}


Freenect2FrameFormat freenect2_frame_get_format(Freenect2FrameRef frame_ref)
{
    Frame* frame = reinterpret_cast<Frame*>(frame_ref);
    return static_cast<Freenect2FrameFormat>(frame->format);
}

Freenect2RegistrationRef freenect2_registration_create(
    IrCameraParams depth_p, ColorCameraParams rgb_p)
{
    return reinterpret_cast<Freenect2RegistrationRef>(
        new Registration(depth_p, rgb_p));
}

void freenect2_registration_dispose(Freenect2RegistrationRef reg_ref)
{
    Registration* reg = reinterpret_cast<Registration*>(reg_ref);
    delete reg;
}

void freenect2_registration_apply(
    Freenect2RegistrationRef reg_ref, Freenect2FrameRef rgb_ref,
    Freenect2FrameRef depth_ref, Freenect2FrameRef undistorted_ref,
    Freenect2FrameRef registered_ref, int enable_filter)
{
    Registration* reg = reinterpret_cast<Registration*>(reg_ref);
    Frame* rgb = reinterpret_cast<Frame*>(rgb_ref);
    Frame* depth = reinterpret_cast<Frame*>(depth_ref);
    Frame* undistorted = reinterpret_cast<Frame*>(undistorted_ref);
    Frame* registered = reinterpret_cast<Frame*>(registered_ref);
    reg->apply(rgb, depth, undistorted, registered, enable_filter);
}

}
''',
    libraries=['freenect2'], source_extension='.cpp',
    include_dirs=[os.path.expanduser('~/.local/include')],
    library_dirs=[os.path.expanduser('~/.local/lib')])

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
    Freenect2FrameRef registered_ref, int enable_filter);
''')

if __name__ == "__main__":
    ffibuilder.compile(verbose=True)
