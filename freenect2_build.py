import os
from cffi import FFI

this_dir = os.path.abspath(os.path.dirname(__file__))

ffibuilder = FFI()

ffibuilder.set_source(
    "freenect2._freenect2", r'''
#include <libfreenect2/libfreenect2.hpp>

typedef void *Freenect2Ref;
typedef void *Freenect2DeviceRef;
typedef void *Freenect2FrameListenerRef;
typedef void *Freenect2FrameRef;

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

typedef int (*Freenect2FrameListenerFunc) (
    Freenect2FrameType type, Freenect2FrameRef frame, void *user_data);
Freenect2FrameListenerRef freenect2_frame_listener_create(
    Freenect2FrameListenerFunc func, void* user_data);
void freenect2_frame_listener_dispose(Freenect2FrameListenerRef fl_ref);

extern "Python" int frame_listener_callback(
    Freenect2FrameType type, Freenect2FrameRef frame, void *user_data);
''')

if __name__ == "__main__":
    ffibuilder.compile(verbose=True)
