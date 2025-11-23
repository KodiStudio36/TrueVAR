"""
gst-launch-1.0 -e videotestsrc ! queue ! x264enc ! tee name=t
    t. ! queue ! mp4mux ! filesink location=output.mp4
    t. ! queue ! h264parse ! avdec_h264 ! videoconvert ! autovideosink

gst-launch-1.0 -e videotestsrc ! decodebin ! videoconvert ! queue ! x264enc ! tee name=t t. ! queue ! mp4mux ! filesink location=output.mp4 t. ! queue ! h264parse ! avdec_h264 ! videoconvert ! autovideosink

videotestsrc ! decodebin ! videoconvert ! queue ! x264enc ! tee name=t t. ! queue ! mp4mux ! filesink location=output.mp4 t. ! queue ! h264parse ! avdec_h264 ! videoconvert ! appsink name=sink emit-signals=true

gst-launch-1.0 -e videotestsrc ! video/x-raw,width=640,height=480,framerate=30/1 ! queue ! x264enc ! tee name=t
    t. ! queue ! rtph264pay ! udpsink host=224.1.1.1 port=20000 auto-multicast=true
    t. ! queue ! h264parse ! splitmuxsink location=./vid%02d.mkv max-size-time=10000000000
    t. ! queue ! h264parse ! avdec_h264 ! videoconvert ! videoscale ! video/x-raw,width=100 ! autovideosink

gst-launch-1.0 -e v4l2src device=/dev/video0 ! "image/jpeg,framerate=30/1,width=640,height=480" ! jpegdec ! videoconvert ! tee name=t t. ! queue ! x264enc tune=zerolatency ! mp4mux ! filesink location=video.mp4 t. ! queue ! videoconvert ! autovideosink

gst-launch-1.0 -e v4l2src device=/dev/video0 ! "image/jpeg,framerate=30/1,width=640,height=480" ! jpegdec ! videoconvert ! queue ! x264enc tune=zerolatency ! mp4mux ! filesink location=video.mp4

gst-launch-1.0 -e v4l2src device=/dev/video0 ! decodebin ! videoconvert ! x264enc ! mp4mux ! filesink location=output.mp4

gst-launch-1.0 -v v4l2src device=/dev/video0 ! videoconvert ! videoscale ! video/x-raw,width=1280,height=720 ! x264enc bitrate=2000 tune=zerolatency ! video/x-h264,profile=main ! flvmux streamable=true name=mux ! rtmpsink location="rtmp://a.rtmp.youtube.com/live2/tm8k-wc2t-h2ek-demw-b044" alsasrc device=hw:2,0 ! audioconvert ! avenc_aac bitrate=128000 ! mux.

gst-launch-1.0 -v v4l2src device=/dev/video0 ! videoconvert ! videoscale ! video/x-raw,width=1280,height=720 ! x264enc bitrate=2000 tune=zerolatency key-int-max=60 ! video/x-h264,profile=main ! flvmux streamable=true name=mux ! rtmpsink location="rtmp://a.rtmp.youtube.com/live2/tm8k-wc2t-h2ek-demw-b044" audiotestsrc wave=silence ! audioconvert ! avenc_aac bitrate=128000 ! mux.

# This shit fuckin' works #
gst-launch-1.0 -e \
    videotestsrc pattern=ball ! video/x-raw,width=1280,height=720 ! videoconvert ! \
    queue ! compositor name=comp1 ! tee name=comp1_tee comp1_tee. ! vaapih264enc ! avimux ! filesink location=output1.avi \
    videotestsrc pattern=smpte ! video/x-raw,width=1280,height=720 ! videoconvert ! \
    queue ! compositor name=comp2 ! vaapih264enc ! avimux ! filesink location=output2.avi \
    videotestsrc pattern=snow ! video/x-raw,width=1280,height=720 ! videoconvert ! \
    queue ! compositor name=comp3 ! vaapih264enc ! avimux ! filesink location=output3.avi \
    v4l2src device=/dev/video0 ! videoscale ! video/x-raw,width=480,height=270 ! \
    queue ! tee name=overlay_tee \
    overlay_tee. ! queue ! comp1. \
    overlay_tee. ! queue ! comp2. \
    overlay_tee. ! queue ! comp3. \
    comp1_tee. ! queue ! videoconvert ! videoscale ! video/x-raw,width=1280,height=720 ! x264enc bitrate=2000 tune=zerolatency key-int-max=60 ! \
    video/x-h264,profile=main ! flvmux streamable=true name=mux ! rtmpsink location="rtmp://a.rtmp.youtube.com/live2/tm8k-wc2t-h2ek-demw-b044" \
    audiotestsrc wave=silence ! mux.

gst-launch-1.0 -e \
    videotestsrc pattern=ball ! video/x-raw,width=1280,height=720 ! videoconvert ! \
    queue ! compositor name=comp1 ! vaapih264enc ! avimux ! filesink location=output1.avi \
    videotestsrc pattern=smpte ! video/x-raw,width=1280,height=720 ! videoconvert ! \
    queue ! compositor name=comp2 ! vaapih264enc ! avimux ! filesink location=output2.avi \
    videotestsrc pattern=snow ! video/x-raw,width=1280,height=720 ! videoconvert ! \
    queue ! compositor name=comp3 ! vaapih264enc ! avimux ! filesink location=output3.avi \
    v4l2src device=/dev/video0 ! videoscale ! video/x-raw,width=480,height=270 ! \
    queue ! tee name=overlay_tee \
    overlay_tee. ! queue ! comp1. \
    overlay_tee. ! queue ! comp2. \
    overlay_tee. ! queue ! comp3.

gst-launch-1.0 -e \
    videotestsrc pattern=ball ! video/x-raw,width=1280,height=720 ! videoconvert ! \
    queue ! compositor name=comp1 ! queue ! videoconvert ! videoscale ! video/x-raw,width=1280,height=720 ! \
    x264enc bitrate=2000 tune=zerolatency key-int-max=60 ! \
    video/x-h264,profile=main ! flvmux streamable=true name=mux ! rtmpsink location="rtmp://a.rtmp.youtube.com/live2/tm8k-wc2t-h2ek-demw-b044" \
    audiotestsrc wave=silence ! mux. \
    v4l2src device=/dev/video0 ! videoscale ! video/x-raw,width=480,height=270 ! queue ! comp1.

gst-launch-1.0 -e \
    videotestsrc ! video/x-raw,width=1280,height=720,framerate=30/1 ! appsink name=camera1 sync=false emit-signals=True \
    videotestsrc ! video/x-raw,width=1280,height=720,framerate=30/1 ! appsink name=camera2 sync=false emit-signals=True \
    videotestsrc ! video/x-raw,width=1280,height=720,framerate=30/1 ! appsink name=camera3 sync=false emit-signals=True
    

# shm video sink #
gst-launch-1.0 v4l2src device=/dev/video0 ! video/x-raw,format=YUY2,width=640,height=480,framerate=30/1 ! timeoverlay ! queue ! shmsink socket-path=/tmp/gst_shm_socket wait-for-connection=false shm-size=200000000


gst-launch-1.0 -e \
    videotestsrc pattern=ball ! video/x-raw,width=1280,height=720 ! videoconvert ! \
    queue ! compositor name=comp1 ! vaapih264enc ! avimux ! filesink location=output1.avi \
    videotestsrc pattern=smpte ! video/x-raw,width=1280,height=720 ! videoconvert ! \
    queue ! compositor name=comp2 ! vaapih264enc ! avimux ! filesink location=output2.avi \
    videotestsrc pattern=snow ! video/x-raw,width=1280,height=720 ! videoconvert ! \
    queue ! compositor name=comp3 ! vaapih264enc ! avimux ! filesink location=output3.avi \
    shmsrc socket-path=/tmp/gst_shm_socket do-timestamp=true is-live=true ! queue ! video/x-raw,format=YUY2,width=640,height=480,framerate=30/1 ! videoconvert ! \
    queue ! tee name=overlay_tee \
    overlay_tee. ! queue ! comp1. \
    overlay_tee. ! queue ! comp2. \
    overlay_tee. ! queue ! comp3.

gst-launch-1.0 -e \
    videotestsrc pattern=ball ! video/x-raw,width=1280,height=720 ! videoconvert ! \
    queue ! compositor name=comp1 ! queue ! videoconvert ! videoscale ! video/x-raw,width=1280,height=720 ! x264enc bitrate=2000 tune=zerolatency key-int-max=60 ! \
    video/x-h264,profile=main ! flvmux streamable=true name=mux ! rtmpsink location="rtmp://a.rtmp.youtube.com/live2/tm8k-wc2t-h2ek-demw-b044" \
    audiotestsrc wave=silence ! mux. \
    shmsrc socket-path=/tmp/gst_shm_socket do-timestamp=true is-live=true ! queue ! video/x-raw,format=YUY2,width=640,height=480,framerate=30/1 ! videoconvert ! queue ! comp1.

    

gst-launch-1.0 -e shmsrc socket-path=/tmp/gst_shm_socket0 do-timestamp=true is-live=true ! video/x-raw,width=640,height=480,framerate=30/1,format=YUY2 ! videoconvert ! videoscale ! video/x-raw,width=480,height=270 ! queue ! tee name=overlay_tee videotestsrc ! video/x-raw,width=1280,height=720,framerate=30/1,format=RGB ! videoconvert ! queue ! compositor name=comp1 ! vaapih264enc ! avimux ! filesink location=/home/kodi/Documents/programs/var/TrueVAR/records/camera1_segment0.avi overlay_tee. ! queue ! comp1. videotestsrc pattern=ball ! video/x-raw,width=1280,height=720,framerate=30/1,format=RGB ! videoconvert ! queue ! compositor name=comp2 ! vaapih264enc ! avimux ! filesink location=/home/kodi/Documents/programs/var/TrueVAR/records/camera2_segment0.avi overlay_tee. ! queue ! comp2. videotestsrc ! video/x-raw,width=1280,height=720,framerate=30/1,format=RGB ! videoconvert ! queue ! compositor name=comp3 ! vaapih264enc ! avimux ! filesink location=/home/kodi/Documents/programs/var/TrueVAR/records/camera3_segment0.avi overlay_tee. ! queue ! comp3.
gst-launch-1.0 -e v4l2src device=/dev/video0 ! video/x-raw,width=640,height=480,framerate=30/1,format=YUY2 ! timeoverlay ! queue ! shmsink socket-path=/tmp/gst_shm_socket0 wait-for-connection=false shm-size=200000000

gst-launch-1.0 -e shmsrc socket-path=/tmp/gst_shm_socket0 do-timestamp=true is-live=true ! video/x-raw,width=640,height=480,framerate=30/1,format=YUY2 ! videoconvert ! videoscale ! video/x-raw,format=RGB,width=272,height=153 ! appsink name=sink emit-signals=True sync=True drop=False




gst-launch-1.0 -e rtspsrc location=rtsp://admin:TaekwondoVAR@169.254.1.1:554 latency=200 ! rtph264depay ! h264parse ! vaapih264dec ! vaapipostproc ! video/x-raw,width=2304,height=1296,framerate=30/1,format=RGBA ! vaapipostproc ! autovideosink

gst-launch-1.0 -e \
    rtspsrc location=rtsp://admin:TaekwondoVAR@169.254.1.1:554 latency=200 ! rtph264depay ! h264parse ! vaapih264dec ! \
    videoconvert ! video/x-raw,width=2304,height=1296,framerate=30/1,format=RGBA ! \
    videoconvert ! queue ! compositor name=comp1 sink_0::xpos=0 sink_0::ypos=0 sink_1::xpos=10 sink_1::ypos=10 ! video/x-raw,width=2304,height=1296 ! vaapih264enc ! avimux ! filesink location=output1.avi \
    videotestsrc pattern=smpte ! video/x-raw,width=1280,height=720,format=RGBA ! videoconvert ! \
    queue ! compositor name=comp2 ! vaapih264enc ! avimux ! filesink location=output2.avi \
    v4l2src device=/dev/video0 ! videoconvert ! videoscale ! video/x-raw,width=480,height=270,format=RGBA ! videoconvert ! \
    queue ! tee name=overlay_tee \
    overlay_tee. ! queue ! comp1. \
    overlay_tee. ! queue ! comp2.

gst-launch-1.0 -e rtspsrc location=rtsp://admin:TaekwondoVAR@169.254.1.1:554 latency=200 ! rtph264depay ! h264parse ! vaapih264dec ! vaapipostproc ! video/x-raw,width=2304,height=1296,framerate=30/1,format=YUY2 ! vaapipostproc ! queue ! shmsink socket-path=/tmp/camera0_shm_socket wait-for-connection=false shm-size=200000000
gst-launch-1.0 -e shmsrc socket-path=/tmp/camera0_shm_socket do-timestamp=true is-live=true ! queue ! video/x-raw,width=2304,height=1296,framerate=30/1,format=YUY2 ! videoconvert ! autovideosink


    
gst-launch-1.0 -e \
    v4l2src device=/dev/video0 ! video/x-raw,width=640,height=480,framerate=30/1,format=YUY2 ! queue ! shmsink socket-path=/tmp/camera0_shm_socket wait-for-connection=false shm-size=200000000 \
    rtspsrc location=rtsp://admin:TaekwondoVAR@169.254.1.1:554 latency=200 ! rtph264depay ! h264parse ! vaapih264dec ! vaapipostproc ! video/x-raw,width=2304,height=1296,framerate=30/1,format=RGBA ! vaapipostproc ! queue ! shmsink socket-path=/tmp/camera0_shm_socket wait-for-connection=false shm-size=200000000 \
    v4l2src device=/dev/video0 ! video/x-raw,width=640,height=480,framerate=30/1,format=YUY2 ! queue ! shmsink socket-path=/tmp/camera0_shm_socket wait-for-connection=false shm-size=200000000 \
    v4l2src device=/dev/video0 ! video/x-raw,width=640,height=480,framerate=30/1,format=YUY2 ! queue ! shmsink socket-path=/tmp/camera0_shm_socket wait-for-connection=false shm-size=200000000

rtspsrc location=rtsp://admin:TaekwondoVAR@169.254.1.1:554 latency=200 ! rtph264depay ! h264parse ! vaapih264dec ! videoconvert    
    

v4l2src device=/dev/video0 ! video/x-raw,width=640,height=480,framerate=30/1,format=YUY2 ! queue ! shmsink socket-path=/tmp/camera0_shm_socket wait-for-connection=false shm-size=200000000 rtspsrc location=rtsp://admin:TaekwondoVAR@169.254.1.1:554 latency=200 ! rtph264depay ! h264parse ! vaapih264dec ! vaapipostproc ! video/x-raw,width=2304,height=1296,framerate=30/1,format=RGBA ! queue ! shmsink socket-path=/tmp/camera1_shm_socket wait-for-connection=false shm-size=200000000 rtspsrc location=rtsp://admin:TaekwondoVAR@169.254.1.2:554 latency=200 ! rtph264depay ! h264parse ! vaapih264dec ! vaapipostproc ! video/x-raw,width=2304,height=1296,framerate=30/1,format=RGBA ! queue ! shmsink socket-path=/tmp/camera2_shm_socket wait-for-connection=false shm-size=200000000 rtspsrc location=rtsp://admin:TaekwondoVAR@169.254.1.3:554 latency=200 ! rtph264depay ! h264parse ! vaapih264dec ! vaapipostproc ! video/x-raw,width=2304,height=1296,framerate=30/1,format=RGBA ! queue ! shmsink socket-path=/tmp/camera3_shm_socket wait-for-connection=false shm-size=200000000
shmsrc socket-path=/tmp/camera0_shm_socket do-timestamp=true is-live=true ! video/x-raw,width=640,height=480,framerate=30/1,format=YUY2 ! videoconvert ! videoscale ! video/x-raw,width=480,height=270 ! queue ! tee name=overlay_tee shmsrc socket-path=/tmp/camera1_shm_socket do-timestamp=true is-live=true ! video/x-raw,width=2304,height=1296,framerate=30/1,format=RGBA ! videoconvert ! videoscale ! video/x-raw,width=1280,height=720 ! queue ! compositor name=comp1 sink_0::xpos=0 sink_0::ypos=0 sink_1::xpos=10 sink_1::ypos=10 ! video/x-raw,width=1280,height=720 ! vaapih264enc ! avimux ! filesink location=/home/kodi/Documents/programs/var/TrueVAR/records/camera1_segment0.avi overlay_tee. ! queue ! comp1. shmsrc socket-path=/tmp/camera2_shm_socket do-timestamp=true is-live=true ! video/x-raw,width=2304,height=1296,framerate=30/1,format=RGBA ! videoconvert ! videoscale ! video/x-raw,width=1280,height=720 ! queue ! compositor name=comp2 sink_0::xpos=0 sink_0::ypos=0 sink_1::xpos=10 sink_1::ypos=10 ! video/x-raw,width=1280,height=720 ! vaapih264enc ! avimux ! filesink location=/home/kodi/Documents/programs/var/TrueVAR/records/camera2_segment0.avi overlay_tee. ! queue ! comp2. shmsrc socket-path=/tmp/camera3_shm_socket do-timestamp=true is-live=true ! video/x-raw,width=2304,height=1296,framerate=30/1,format=RGBA ! videoconvert ! videoscale ! video/x-raw,width=1280,height=720 ! queue ! compositor name=comp3 sink_0::xpos=0 sink_0::ypos=0 sink_1::xpos=10 sink_1::ypos=10 ! video/x-raw,width=1280,height=720 ! vaapih264enc ! avimux ! filesink location=/home/kodi/Documents/programs/var/TrueVAR/records/camera3_segment0.avi overlay_tee. ! queue ! comp3.

gst-launch-1.0 -e \
    rtspsrc location=rtsp://admin:TaekwondoVAR@169.254.1.1:554 latency=200 ! rtph264depay ! h264parse ! vaapih264dec ! vaapipostproc ! video/x-raw,width=2304,height=1296,framerate=30/1,format=RGBA ! vaapipostproc ! queue ! vaapih264enc bitrate=30000 ! avimux ! filesink location=output1.avi \
    rtspsrc location=rtsp://admin:TaekwondoVAR@169.254.1.2:554 latency=200 ! rtph264depay ! h264parse ! vaapih264dec ! vaapipostproc ! video/x-raw,width=2304,height=1296,framerate=30/1,format=RGBA ! vaapipostproc ! queue ! vaapih264enc bitrate=30000 ! avimux ! filesink location=output2.avi \
    rtspsrc location=rtsp://admin:TaekwondoVAR@169.254.1.3:554 latency=200 ! rtph264depay ! h264parse ! vaapih264dec ! vaapipostproc ! video/x-raw,width=2304,height=1296,framerate=30/1,format=RGBA ! vaapipostproc ! queue ! vaapih264enc bitrate=30000 ! avimux ! filesink location=output3.avi





gst-launch-1.0 -e \
    v4l2src device=/dev/video0 ! video/x-raw,width=640,height=480,framerate=30/1,format=YUY2 ! \
        queue ! shmsink socket-path=/tmp/camera0_shm_socket wait-for-connection=false shm-size=200000000 \
    videotestsrc pattern=ball ! video/x-raw,width=1280,height=720,framerate=30/1,format=RGBA ! \
        queue ! shmsink socket-path=/tmp/camera1_shm_socket wait-for-connection=false shm-size=200000000 \
    videotestsrc pattern=ball ! video/x-raw,width=1280,height=720,framerate=30/1,format=RGBA ! \
        queue ! shmsink socket-path=/tmp/camera2_shm_socket wait-for-connection=false shm-size=200000000 \
    videotestsrc pattern=ball ! video/x-raw,width=1280,height=720,framerate=30/1,format=RGBA ! \
        queue ! shmsink socket-path=/tmp/camera3_shm_socket wait-for-connection=false shm-size=200000000





gst-launch-1.0 -e \
    shmsrc socket-path=/tmp/camera0_shm_socket do-timestamp=true is-live=true ! video/x-raw,width=640,height=480,framerate=30/1,format=YUY2,interlace-mode=progressive ! \
        vaapipostproc ! video/x-raw,width=320,height=240 ! queue max-size-buffers=2 ! tee name=overlay_tee \
    shmsrc socket-path=/tmp/camera1_shm_socket do-timestamp=true is-live=true ! video/x-raw,width=1280,height=720,framerate=30/1,format=RGBA,interlace-mode=progressive ! \
        vaapipostproc ! video/x-raw,width=1280,height=720 ! queue max-size-buffers=4 ! \
        compositor name=comp1 sink_0::xpos=0 sink_0::ypos=0 sink_1::xpos=10 sink_1::ypos=10 ! video/x-raw,width=1280,height=720 ! \
        vaapih264enc bitrate=5000 ! avimux ! filesink location=/home/kodi/Documents/programs/var/TrueVAR/records/camera1_segment0.avi \
        overlay_tee. ! queue ! comp1. \
    shmsrc socket-path=/tmp/camera2_shm_socket do-timestamp=true is-live=true ! video/x-raw,width=1280,height=720,framerate=30/1,format=RGBA,interlace-mode=progressive ! \
        vaapipostproc ! video/x-raw,width=1280,height=720 ! queue max-size-buffers=4 ! \
        compositor name=comp2 sink_0::xpos=0 sink_0::ypos=0 sink_1::xpos=10 sink_1::ypos=10 ! video/x-raw,width=1280,height=720 ! \
        vaapih264enc bitrate=5000 ! avimux ! filesink location=/home/kodi/Documents/programs/var/TrueVAR/records/camera2_segment0.avi \
        overlay_tee. ! queue ! comp2. \
    shmsrc socket-path=/tmp/camera3_shm_socket do-timestamp=true is-live=true ! video/x-raw,width=1280,height=720,framerate=30/1,format=RGBA,interlace-mode=progressive ! \
        vaapipostproc ! video/x-raw,width=1280,height=720 ! queue max-size-buffers=4 ! \
        compositor name=comp3 sink_0::xpos=0 sink_0::ypos=0 sink_1::xpos=10 sink_1::ypos=10 ! video/x-raw,width=1280,height=720 ! \
        vaapih264enc bitrate=5000 ! avimux ! filesink location=/home/kodi/Documents/programs/var/TrueVAR/records/camera3_segment0.avi \
        overlay_tee. ! queue ! comp3.

gst-launch-1.0 -e \
    shmsrc socket-path=/tmp/camera0_shm_socket do-timestamp=true is-live=true ! video/x-raw,width=640,height=480,framerate=30/1,format=YUY2,interlace-mode=progressive ! \
        vaapipostproc ! video/x-raw,width=1280,height=720 ! queue max-size-buffers=4 leaky=downstream ! \
        compositor name=comp sink_0::xpos=0 sink_0::ypos=0 sink_1::xpos=1280 sink_1::ypos=0 sink_2::xpos=0 sink_2::ypos=720 sink_3::xpos=1280 sink_3::ypos=720 ! video/x-raw,width=2560,height=1440 ! \
        vaapih264enc bitrate=5000 ! avimux ! filesink location=output.avi \
    shmsrc socket-path=/tmp/camera1_shm_socket do-timestamp=true is-live=true ! video/x-raw,width=1280,height=720,framerate=30/1,format=RGBA,interlace-mode=progressive ! \
        vaapipostproc ! queue max-size-buffers=4 leaky=downstream ! comp. \
    shmsrc socket-path=/tmp/camera2_shm_socket do-timestamp=true is-live=true ! video/x-raw,width=1280,height=720,framerate=30/1,format=RGBA,interlace-mode=progressive ! \
        vaapipostproc ! queue max-size-buffers=4 leaky=downstream ! comp. \
    shmsrc socket-path=/tmp/camera3_shm_socket do-timestamp=true is-live=true ! video/x-raw,width=1280,height=720,framerate=30/1,format=RGBA,interlace-mode=progressive ! \
        vaapipostproc ! queue max-size-buffers=4 leaky=downstream ! comp.

gst-launch-1.0 -e \
    v4l2src device=/dev/video0 ! video/x-raw,width=640,height=480,framerate=30/1,format=YUY2 ! vaapipostproc ! \
    video/x-raw,width=1280,height=2000 ! vaapih264enc bitrate=5000 ! avimux ! filesink location=output.avi

gst-launch-1.0 \
    compositor name=comp sink_0::xpos=640 sink_0::ypos=0 sink_1::xpos=640 sink_1::ypos=720 ! video/x-raw,width=2560,height=1440 ! \
        vaapipostproc ! x264enc bitrate=2000 tune=zerolatency key-int-max=60 ! \
        video/x-h264,profile=main ! flvmux streamable=true name=mux ! rtmpsink location="rtmp://a.rtmp.youtube.com/live2/tm8k-wc2t-h2ek-demw-b044" \
        audiotestsrc wave=silence ! mux. \
    videotestsrc ! video/x-raw,width=1280,height=720,framerate=30/1,format=RGBA,interlace-mode=progressive ! \
        vaapipostproc ! queue ! comp. \
    videotestsrc pattern=ball ! video/x-raw,width=1280,height=720,framerate=30/1,format=RGBA,interlace-mode=progressive ! \
        vaapipostproc ! queue ! comp.

x264enc bitrate=2000 tune=zerolatency key-int-max=60 ! \
video/x-h264,profile=main ! flvmux streamable=true name=mux ! rtmpsink location="rtmp://a.rtmp.youtube.com/live2/tm8k-wc2t-h2ek-demw-b044" \
audiotestsrc wave=silence ! mux. \
shmsrc socket-path=/tmp/gst_shm_socket do-timestamp=true is-live=true ! queue ! video/x-raw,format=YUY2,width=640,height=480,framerate=30/1 ! videoconvert ! queue ! comp1.

gst-launch-1.0 \
rtspsrc location=rtsp://admin:TaekwondoVAR@192.168.0.21:554 latency=800 ! rtph264depay ! h264parse ! vaapih264dec ! vaapipostproc ! video/x-raw,width=1280,height=720,framerate=30/1,format=RGBA,interlace-mode=progressive ! vaapipostproc ! \
queue ! compositor name=comp1 ! queue ! videoconvert ! x264enc bitrate=2000 tune=zerolatency key-int-max=60 ! \
video/x-h264,profile=main ! flvmux streamable=true name=mux ! rtmpsink location="rtmp://a.rtmp.youtube.com/live2/ze78-gupd-46hc-bseb-4hq4" \
audiotestsrc wave=silence ! mux. \
v4l2src device=/dev/video0 ! image/jpeg,width=640,height=480,framerate=30/1 ! jpegdec ! vaapipostproc ! video/x-raw,width=640,height=480,framerate=30/1,format=RGBA,interlace-mode=progressive ! vaapipostproc ! video/x-raw,width=320,height=200 ! comp1.

gst-launch-1.0 -e \
    videotestsrc ! video/x-raw,width=1280,height=720,framerate=30/1,format=RGBA,interlace-mode=progressive ! vaapipostproc ! \
    queue ! compositor name=comp1 sink_0::xpos=0 sink_0::ypos=0 sink_1::xpos=10 sink_1::ypos=10 ! video/x-raw,width=1280,height=720 ! x264enc bitrate=2000 tune=zerolatency key-int-max=60 ! \
    video/x-h264,profile=main ! flvmux streamable=true name=mux ! rtmpsink location="rtmp://a.rtmp.youtube.com/live2/ze78-gupd-46hc-bseb-4hq4" \
    audiotestsrc wave=silence ! mux. \
    videotestsrc ! video/x-raw,width=640,height=480,framerate=30/1,format=RGBA,interlace-mode=progressive ! vaapipostproc ! video/x-raw,width=320,height=200 ! comp1.

gst-launch-1.0 rtspsrc location=rtsp://admin:TaekwondoVAR@192.168.0.21:554 latency=800 ! rtph264depay ! h264parse ! vaapih264dec ! vaapipostproc ! video/x-raw,format=RGBA,width=1280,height=720,framerate=30/1 ! timeoverlay ! queue ! shmsink socket-path=/tmp/gst_shm_socket wait-for-connection=false shm-size=200000000

videotestsrc ! vaapipostproc ! video/x-raw,width=1280,height=720,framerate=30/1,format=NV12 ! capsfilter ! queue ! shmsink socket-path=/tmp/camera1_shm_socket wait-for-connection=false shm-size=200000000 
videotestsrc ! vaapipostproc ! video/x-raw,width=1280,height=720,framerate=30/1,format=NV12 ! capsfilter ! queue ! shmsink socket-path=/tmp/camera2_shm_socket wait-for-connection=false shm-size=200000000 
videotestsrc ! vaapipostproc ! video/x-raw,width=1280,height=720,framerate=30/1,format=NV12 ! capsfilter ! queue ! shmsink socket-path=/tmp/camera3_shm_socket wait-for-connection=false shm-size=200000000

gst-launch-1.0 -e \
    wpesrc location=https://example.com draw-background=false ! video/x-raw,width=640,height=480,framerate=30/1,format=NV12 ! queue leaky=downstream ! vaapipostproc ! video/x-raw,width=320,height=180 ! tee name=overlay_tee \
    videotestsrc ! vaapipostproc ! video/x-raw,width=1280,height=720,framerate=30/1,format=NV12 ! queue leaky=downstream ! vaapipostproc ! compositor name=comp2 sink_0::xpos=0 sink_0::ypos=0 sink_1::xpos=10 sink_1::ypos=10 ! video/x-raw,width=1280,height=720 ! vaapih264enc bitrate=4000 ! avimux ! filesink location=/home/kodi/Documents/programs/var/TrueVAR/records/id3347.9_camera1_segment0.avi overlay_tee. ! queue ! comp2. \
    videotestsrc ! vaapipostproc ! video/x-raw,width=1280,height=720,framerate=30/1,format=NV12 ! queue leaky=downstream ! vaapipostproc ! compositor name=comp3 sink_0::xpos=0 sink_0::ypos=0 sink_1::xpos=10 sink_1::ypos=10 ! video/x-raw,width=1280,height=720 ! vaapih264enc bitrate=4000 ! avimux ! filesink location=/home/kodi/Documents/programs/var/TrueVAR/records/id3347.9_camera2_segment0.avi overlay_tee. ! queue ! comp3. \
    videotestsrc ! vaapipostproc ! video/x-raw,width=1280,height=720,framerate=30/1,format=NV12 ! queue leaky=downstream ! vaapipostproc ! compositor name=comp4 sink_0::xpos=0 sink_0::ypos=0 sink_1::xpos=10 sink_1::ypos=10 ! video/x-raw,width=1280,height=720 ! vaapih264enc bitrate=4000 ! avimux ! filesink location=/home/kodi/Documents/programs/var/TrueVAR/records/id3347.9_camera3_segment0.avi overlay_tee. ! queue ! comp4.

gst-launch-1.0 -e \
                         wpesrc location=http://localhost:8000/scoreboard draw-background=true ! vaapipostproc ! video/x-raw,width=320,height=180,format=RGBA ! \
                             tee name=overlay_tee \
                         \
                         videotestsrc ! vaapipostproc ! video/x-raw,width=1280,height=720,framerate=30/1,format=RGBA ! \
                             queue leaky=downstream ! vaapipostproc ! \
                             compositor name=comp2 sink_0::xpos=0 sink_0::ypos=0 sink_1::xpos=10 sink_1::ypos=10 ! \
                             video/x-raw,width=1280,height=720 ! \
                             vaapisink \
                             overlay_tee. ! queue ! comp2. \
                         \
                         videotestsrc ! vaapipostproc ! video/x-raw,width=1280,height=720,framerate=30/1,format=RGBA ! \
                             queue leaky=downstream ! vaapipostproc ! \
                             compositor name=comp3 sink_0::xpos=0 sink_0::ypos=0 sink_1::xpos=10 sink_1::ypos=10 ! \
                             video/x-raw,width=1280,height=720 ! \
                             vaapisink \
                             overlay_tee. ! queue ! comp3. \
                         \
                         videotestsrc ! vaapipostproc ! video/x-raw,width=1280,height=720,framerate=30/1,format=RGBA ! \
                             queue leaky=downstream ! vaapipostproc ! \
                             compositor name=comp4 sink_0::xpos=0 sink_0::ypos=0 sink_1::xpos=10 sink_1::ypos=10 ! \
                             video/x-raw,width=1280,height=720 ! \
                             vaapisink \
                             overlay_tee. ! queue ! comp4.

create scoreboard
    """

"""
shmsrc socket-path={shmsrc_socket} do-timestamp=true is-live=true \
    ! video/x-raw,format=NV12,width=1280,height=720,framerate=30/1 \
    ! videoconvert \
    ! xvimagesink name=extsink force-aspect-ratio=true
"""