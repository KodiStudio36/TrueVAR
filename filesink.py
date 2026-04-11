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
gst-launch-1.0 -e \
v4l2src device=/dev/video0 ! image/jpeg,width=1280,height=720,framerate=30/1 ! vaapijpegdec ! queue leaky=2 max-size-buffers=1 ! vaapipostproc ! \
    video/x-raw,width=1280,height=720,framerate=30/1,format=NV12 ! tee name=scoreboard_tee \
scoreboard_tee. vaapisink name=mysink xid-usage=auto window-class="mysink" window-title="External Preview" \
scoreboard_tee. shmsink socket-path=/tmp/camera0_shm_socket wait-for-connection=false shm-size=200000000

gst-launch-1.0 -e \
v4l2src device=/dev/video0 ! image/jpeg,width=1280,height=720,framerate=30/1 \
    ! vaapijpegdec ! vaapipostproc ! video/x-raw,width=1280,height=720,framerate=30/1,format=NV12 \
    ! tee name=scoreboard_tee \
scoreboard_tee. ! queue leaky=downstream max-size-buffers=1 \
    ! xvimagesink name=extsink force-aspect-ratio=true \
scoreboard_tee. ! queue leaky=downstream max-size-buffers=1 \
    ! shmsink socket-path=/tmp/camera0_shm_socket wait-for-connection=false shm-size=200000000

gst-launch-1.0 -e \
shmsrc socket-path=/tmp/camera0_shm_socket do-timestamp=true is-live=true ! \
    video/x-raw,width=1280,height=720,framerate=30/1,format=NV12,interlace-mode=progressive ! \
    queue leaky=downstream ! vaapipostproc ! video/x-raw,width=320,height=180 ! tee name=overlay_tee  \
videotestsrc ! vaapipostproc ! video/x-raw,width=1280,height=720,framerate=30/1,format=NV12,interlace-mode=progressive ! queue ! \
    compositor name=comp1 sink_0::xpos=0 sink_0::ypos=0 sink_1::xpos=10 sink_1::ypos=10 ! video/x-raw,width=1280,height=720 ! \
    vaapih264enc bitrate=4000 ! avimux ! filesink location=test1.avi \
overlay_tee. ! queue ! comp1. \
videotestsrc ! vaapipostproc ! video/x-raw,width=1280,height=720,framerate=30/1,format=NV12,interlace-mode=progressive ! queue ! \
    compositor name=comp2 sink_0::xpos=0 sink_0::ypos=0 sink_1::xpos=10 sink_1::ypos=10 ! video/x-raw,width=1280,height=720 ! \
    vaapih264enc bitrate=4000 ! avimux ! filesink location=test2.avi \
overlay_tee. ! queue ! comp2. \
videotestsrc ! vaapipostproc ! video/x-raw,width=1280,height=720,framerate=30/1,format=NV12,interlace-mode=progressive ! queue ! \
    compositor name=comp3 sink_0::xpos=0 sink_0::ypos=0 sink_1::xpos=10 sink_1::ypos=10 ! video/x-raw,width=1280,height=720 ! \
    vaapih264enc bitrate=4000 ! avimux ! filesink location=test3.avi \
overlay_tee. ! queue ! comp3.

gst-launch-1.0 -e \
shmsrc socket-path=/tmp/camera0_shm_socket do-timestamp=true is-live=true \
    ! video/x-raw,format=NV12,width=1280,height=720,framerate=30/1,interlace-mode=progressive \
    ! queue leaky=downstream \
    ! videoconvert \
    ! xvimagesink name=extsink force-aspect-ratio=true
    
gst-launch-1.0 -e \
shmsrc socket-path=/tmp/camera0_shm_socket do-timestamp=true is-live=true \
    ! video/x-raw,format=NV12,width=1280,height=720,framerate=30/1,interlace-mode=progressive \
    ! queue leaky=downstream max-size-buffers=1 \
    ! vaapisink name=mysink xid-usage=auto window-class="mysink" window-title="External Preview"

gst-launch-1.0 -e \
shmsrc socket-path=/tmp/camera0_shm_socket do-timestamp=true is-live=true ! \
    video/x-raw,width=1280,height=720,framerate=30/1,format=NV12,interlace-mode=progressive ! \
    queue leaky=downstream ! vaapipostproc ! video/x-raw,width=320,height=180 ! tee name=overlay_tee  \
rtspsrc location=rtsp://admin:TaekwondoVAR@myip1:554 latency=800 ! rtph264depay ! h264parse ! vaapih264dec ! vaapipostproc ! video/x-raw,width=1280,height=720,framerate=30/1,format=NV12,interlace-mode=progressive ! queue ! \
    compositor name=comp1 sink_0::xpos=0 sink_0::ypos=0 sink_1::xpos=10 sink_1::ypos=10 ! video/x-raw,width=1280,height=720 ! \
    vaapih264enc bitrate=4000 ! avimux ! filesink location=test1.avi \
overlay_tee. ! queue ! comp1. \
rtspsrc location=rtsp://admin:TaekwondoVAR@myip2:554 latency=800 ! rtph264depay ! h264parse ! vaapih264dec ! vaapipostproc ! video/x-raw,width=1280,height=720,framerate=30/1,format=NV12,interlace-mode=progressive ! queue ! \
    compositor name=comp2 sink_0::xpos=0 sink_0::ypos=0 sink_1::xpos=10 sink_1::ypos=10 ! video/x-raw,width=1280,height=720 ! \
    vaapih264enc bitrate=4000 ! avimux ! filesink location=test2.avi \
overlay_tee. ! queue ! comp2. \
rtspsrc location=rtsp://admin:TaekwondoVAR@myip3:554 latency=800 ! rtph264depay ! h264parse ! vaapih264dec ! vaapipostproc ! video/x-raw,width=1280,height=720,framerate=30/1,format=NV12,interlace-mode=progressive ! queue ! \
    compositor name=comp3 sink_0::xpos=0 sink_0::ypos=0 sink_1::xpos=10 sink_1::ypos=10 ! video/x-raw,width=1280,height=720 ! \
    vaapih264enc bitrate=4000 ! avimux ! filesink location=test3.avi \
overlay_tee. ! queue ! comp3.
    
gst-launch-1.0 -e \
    \
    # --- Scoreboard Source (Camera 0) --- \
    v4l2src device=/dev/video0 \
    ! image/jpeg,width=1280,height=720,framerate=30/1 \
    ! vaapijpegdec \
    ! vaapipostproc \
    ! video/x-raw,width=1280,height=720,framerate=30/1,format=NV12 \
    ! shmsink socket-path=/tmp/camera0_shm_socket wait-for-connection=false shm-size=200000000 sync=false async=false\
\
    # --- Camera 1 Source to SHM --- \
    videotestsrc ! vaapipostproc \
    ! video/x-raw,width=1280,height=720,framerate=30/1,format=NV12 ! queue leaky=downstream max-size-buffers=1 \
    ! shmsink socket-path=/tmp/camera1_shm_socket wait-for-connection=false shm-size=200000000 sync=false async=false \
    \
    # --- Camera 2 Source to SHM --- \
    videotestsrc ! vaapipostproc \
    ! video/x-raw,width=1280,height=720,framerate=30/1,format=NV12 ! queue leaky=downstream max-size-buffers=1 \
    ! shmsink socket-path=/tmp/camera2_shm_socket wait-for-connection=false shm-size=200000000 sync=false async=false \
    \
    # --- Camera 3 Source to SHM --- \
    videotestsrc ! vaapipostproc \
    ! video/x-raw,width=1280,height=720,framerate=30/1,format=NV12 ! queue leaky=downstream max-size-buffers=1 \
    ! shmsink socket-path=/tmp/camera3_shm_socket wait-for-connection=false shm-size=200000000 sync=false async=false

    gst-launch-1.0 -e \
    \
v4l2src device=/dev/video0 ! image/jpeg,width=1280,height=720,framerate=30/1 ! vaapijpegdec ! vaapipostproc ! video/x-raw,width=1280,height=720,framerate=30/1,format=NV12 ! \
tee name=t t. ! queue leaky=downstream max-size-buffers=1 ! shmsink socket-path=/tmp/camera0_shm_socket wait-for-connection=false shm-size=200000000 sync=false async=false \
videotestsrc ! vaapipostproc ! video/x-raw,width=1280,height=720,framerate=/1,format=NV12 ! queue leaky=downstream max-size-buffers=1 ! shmsink socket-path=/tmp/camera1_shm_socket wait-for-connection=false shm-size=200000000 sync=false async=false \
videotestsrc ! vaapipostproc ! video/x-raw,width=1280,height=720,framerate=/1,format=NV12 ! queue leaky=downstream max-size-buffers=1 ! shmsink socket-path=/tmp/camera2_shm_socket wait-for-connection=false shm-size=200000000 sync=false async=false \
videotestsrc ! vaapipostproc ! video/x-raw,width=1280,height=720,framerate=/1,format=NV12 ! queue leaky=downstream max-size-buffers=1 ! shmsink socket-path=/tmp/camera3_shm_socket wait-for-connection=false shm-size=200000000 sync=false async=false

42["message",{"op":"event.scoring.getAdminPair","d":{"success":true,"pair":{"id":5336192,"event_id":11534,"division_id":15113,"group_id":null,"category_id":831904,"sp1_id":338462,"sp2_id":338464,"leftId":0,"rightId":0,"loseLeftId":0,"loseRightId":0,"winner_id":0,"score_one":10,"score_two":10,"priority_score":0,"winner_n":0,"is_final":0,"serial":4,"win_type_id":1,"number":1,"type":0,"court":1,"warnings_one":0,"warnings_two":0,"currentRoundTime":"00:00","currentRoundNumber":1,"currentRoundType":1,"currentRoundStatus":0,"lastStartTime":"2026-04-10T22:37:08.000Z","is_finished":0,"faultsOne":0,"faultsTwo":0,"is_active":1,"day":1,"set_score_time":0,"place":2,"area_id":16479,"is_single":0,"is_team":0,"settings_id":34807,"start_time":"00:00","canceled":0,"disq1":0,"disq2":0,"is_fake":0,"stage_id":0,"group_number":0,"stage_number":0,"spent_time":0,"pool_id":38689,"seed1":9,"seed2":8,"locked":0,"euid":0,"rounds":null,"round":0,"custom_start_time":-1,"details":null,"tiebreak":0,"draw_type":1,"color1":"blue","color2":"red","area_token":"gyeqbjtzfs","fullTitle":"Individual Poomsae, Class D: 9. - 7. Gup , Seniors under 40 1985-1994, Male","user1":{"user":{"id":338462,"name":"Stephen","surname":"Thompson","link":null,"image_url":"","gender":1,"birthdate":"1985-01-01"},"academy":"","org":{"image_url":"","title":"Infinity Sports","link":null,"id":4139,"country_code":"FR"},"metadata":null},"user2":{"user":{"id":338464,"name":"Constantine","surname":"Turner","link":null,"image_url":"","gender":1,"birthdate":"1985-01-01"},"academy":"","org":{"image_url":"","title":"Phoenix Sports","link":null,"id":4803,"country_code":"ZA"},"metadata":null},"settings":{"sportId":0,"type":"sparring","hasRounds":true,"rounds":2,"roundTime":90,"restTime":0,"hasRoundsToWin":false,"roundsToWin":2,"doctorTime":0,"doctorType":0,"hasPenalty":false,"scorePerWarnings":1,"warningsAffectTo":1,"warningsQtyToAction":4,"warningsQtyToPenalty":-1,"warningsStartFrom":0,"penaltyPerWarningsQty":0,"scorePerPenalty":1,"penaltyAffectTo":1,"maxPenalty":2,"judges":5,"resultType":1,"startScorePoint":0,"scoringMethod":1,"attempts":2,"maxQuantity":2,"maxWinnersTV":10,"scoringType":1,"inputScoringValues":["1","2","3"],"hasExtraRound":false,"extraRoundTime":60,"extraRoundResetAll":false,"hasGoldenRound":false,"goldenRoundTime":60,"goldenRoundResetAll":false,"showJudgesOnTv":true,"hasTimers":false,"multipleTimers":false,"clearBreakpoints":false,"timers":[],"diffScoreToWin":0,"firstScoreToWin":0,"diffScoreToWinGolden":1,"diffScoreToWinExtra":0,"hasProgram":true,"hasDancePrograms":false,"programValues":[],"dancePrograms":[],"competitionType":2,"programParams":{"cutoff":true,"average":true,"programs":[{"id":9828,"title":"Accuracy","subprograms":[{"id":12881,"title":"Accuracy","buttons":["0.3","0.1"],"maxValue":4,"minValue":0,"scoringType":-1,"initialValue":4}]},{"id":9829,"title":"Presentation","subprograms":[{"id":12882,"title":"Strength and speed","buttons":["0.3","0.1"],"maxValue":2,"minValue":0,"scoringType":-1,"initialValue":2},{"id":12883,"title":"Rhythm and coordination","buttons":["0.5"],"maxValue":2,"minValue":0,"scoringType":-1,"initialValue":2},{"id":12884,"title":"Energy expression","buttons":["0.5"],"maxValue":2,"minValue":0,"scoringType":-1,"initialValue":2}]}]},"editable":true,"freeJudgeMode":true,"showScoreOnJoystick":true,"judgeSingleRound":false,"needBreakTime":0,"needRoundWinner":false,"showTVScore":false,"rule_id":0,"screen_id":84,"parent_id":270},"with_music":0,"data":{"id":226156,"round_id":2,"game_id":1,"pair_id":5336192,"timer_start_time":0,"timer_stop_time":0,"time_left":0,"temp_time_left":0,"is_pause":1,"current_round_key":"","warnings":{"rounds":[],"total1":0,"total2":0},"penalties":{"rounds":[],"total1":0,"total2":0},"rounds":[{"f":false,"r":1},{"f":false,"r":2}],"judges_scores":{"rounds":[{"sp_id":338462,"r":2,"j":1,"p":12881,"s":-1.2},{"sp_id":338462,"r":2,"j":1,"p":12882,"s":-0.8},{"sp_id":338462,"r":2,"j":1,"p":12883,"s":-1.1},{"sp_id":338462,"r":2,"j":1,"p":12884,"s":-1.4},{"sp_id":338462,"r":2,"j":2,"p":12881,"s":0},{"sp_id":338462,"r":2,"j":2,"p":12882,"s":0},{"sp_id":338462,"r":2,"j":2,"p":12883,"s":0},{"sp_id":338462,"r":2,"j":2,"p":12884,"s":0},{"sp_id":338462,"r":2,"j":3,"p":12881,"s":0},{"sp_id":338462,"r":2,"j":3,"p":12882,"s":0},{"sp_id":338462,"r":2,"j":3,"p":12883,"s":0},{"sp_id":338462,"r":2,"j":3,"p":12884,"s":0},{"sp_id":338462,"r":2,"j":4,"p":12881,"s":0},{"sp_id":338462,"r":2,"j":4,"p":12882,"s":0},{"sp_id":338462,"r":2,"j":4,"p":12883,"s":0},{"sp_id":338462,"r":2,"j":4,"p":12884,"s":0},{"sp_id":338462,"r":2,"j":5,"p":12881,"s":0},{"sp_id":338462,"r":2,"j":5,"p":12882,"s":0},{"sp_id":338462,"r":2,"j":5,"p":12883,"s":0},{"sp_id":338462,"r":2,"j":5,"p":12884,"s":0},{"sp_id":338462,"r":1,"j":1,"p":12881,"s":-1.2},{"sp_id":338462,"r":1,"j":1,"p":12882,"s":-0.4},{"sp_id":338462,"r":1,"j":1,"p":12883,"s":-0.5},{"sp_id":338462,"r":1,"j":1,"p":12884,"s":-0.6},{"sp_id":338462,"r":1,"j":2,"p":12881,"s":0},{"sp_id":338462,"r":1,"j":2,"p":12882,"s":0},{"sp_id":338462,"r":1,"j":2,"p":12883,"s":0},{"sp_id":338462,"r":1,"j":2,"p":12884,"s":0},{"sp_id":338462,"r":1,"j":3,"p":12881,"s":0},{"sp_id":338462,"r":1,"j":3,"p":12882,"s":0},{"sp_id":338462,"r":1,"j":3,"p":12883,"s":0},{"sp_id":338462,"r":1,"j":3,"p":12884,"s":0},{"sp_id":338462,"r":1,"j":4,"p":12881,"s":0},{"sp_id":338462,"r":1,"j":4,"p":12882,"s":0},{"sp_id":338462,"r":1,"j":4,"p":12883,"s":0},{"sp_id":338462,"r":1,"j":4,"p":12884,"s":0},{"sp_id":338462,"r":1,"j":5,"p":12881,"s":0},{"sp_id":338462,"r":1,"j":5,"p":12882,"s":0},{"sp_id":338462,"r":1,"j":5,"p":12883,"s":0},{"sp_id":338462,"r":1,"j":5,"p":12884,"s":0},{"sp_id":338464,"r":2,"j":1,"p":12881,"s":-1.1},{"sp_id":338464,"r":2,"j":1,"p":12882,"s":-0.7},{"sp_id":338464,"r":2,"j":1,"p":12883,"s":-1},{"sp_id":338464,"r":2,"j":1,"p":12884,"s":-1.3},{"sp_id":338464,"r":2,"j":2,"p":12881,"s":0},{"sp_id":338464,"r":2,"j":2,"p":12882,"s":0},{"sp_id":338464,"r":2,"j":2,"p":12883,"s":0},{"sp_id":338464,"r":2,"j":2,"p":12884,"s":0},{"sp_id":338464,"r":2,"j":3,"p":12881,"s":0},{"sp_id":338464,"r":2,"j":3,"p":12882,"s":0},{"sp_id":338464,"r":2,"j":3,"p":12883,"s":0},{"sp_id":338464,"r":2,"j":3,"p":12884,"s":0},{"sp_id":338464,"r":2,"j":4,"p":12881,"s":0},{"sp_id":338464,"r":2,"j":4,"p":12882,"s":0},{"sp_id":338464,"r":2,"j":4,"p":12883,"s":0},{"sp_id":338464,"r":2,"j":4,"p":12884,"s":0},{"sp_id":338464,"r":2,"j":5,"p":12881,"s":0},{"sp_id":338464,"r":2,"j":5,"p":12882,"s":0},{"sp_id":338464,"r":2,"j":5,"p":12883,"s":0},{"sp_id":338464,"r":2,"j":5,"p":12884,"s":0},{"sp_id":338464,"r":1,"j":1,"p":12881,"s":-0.8},{"sp_id":338464,"r":1,"j":1,"p":12882,"s":-0.8},{"sp_id":338464,"r":1,"j":1,"p":12883,"s":-1},{"sp_id":338464,"r":1,"j":1,"p":12884,"s":-1.2},{"sp_id":338464,"r":1,"j":2,"p":12881,"s":0},{"sp_id":338464,"r":1,"j":2,"p":12882,"s":0},{"sp_id":338464,"r":1,"j":2,"p":12883,"s":0},{"sp_id":338464,"r":1,"j":2,"p":12884,"s":0},{"sp_id":338464,"r":1,"j":3,"p":12881,"s":0},{"sp_id":338464,"r":1,"j":3,"p":12882,"s":0},{"sp_id":338464,"r":1,"j":3,"p":12883,"s":0},{"sp_id":338464,"r":1,"j":3,"p":12884,"s":0},{"sp_id":338464,"r":1,"j":4,"p":12881,"s":0},{"sp_id":338464,"r":1,"j":4,"p":12882,"s":0},{"sp_id":338464,"r":1,"j":4,"p":12883,"s":0},{"sp_id":338464,"r":1,"j":4,"p":12884,"s":0},{"sp_id":338464,"r":1,"j":5,"p":12881,"s":0},{"sp_id":338464,"r":1,"j":5,"p":12882,"s":0},{"sp_id":338464,"r":1,"j":5,"p":12883,"s":0},{"sp_id":338464,"r":1,"j":5,"p":12884,"s":0}],"total1":0,"total2":0},"judges_confirm":[{"sp_id":0,"confirm":true,"round_id":1,"judge_number":1},{"sp_id":0,"confirm":true,"round_id":2,"judge_number":1}],"created_at":1775849354,"is_finished":0,"timers_data":[],"doctor_time1":0,"doctor_time2":0,"nextRoundKey":"","is_rest":0,"is_doctor":0,"is_doctor1":0,"is_doctor2":0,"is_round":1,"custom_scores":[],"program_id":0,"hide_tv":1,"is_gong":1,"settings_id":0,"is_reverse":0,"active_id":0,"auto_start":0,"display_round_id":0,"programs":{"rounds":[{"r":1,"id":511,"sp_id":0,"title":"Koryo"}]},"is_swap":0,"is_swap_tv":0,"other_scores":[],"concurrent_judges":[],"last_end_time":1775867734302,"tv_mode":"full-result","mode2":"","attempt_id":1,"scores_history":[],"other":{},"temp":{"last_pause_time":1775867734302},"finalResults":{"1":{"338462":{"judgesPrograms":[{"r":1,"p":9828,"j":1,"s":2.8},{"r":1,"p":9829,"j":1,"s":4.5},{"r":1,"p":9828,"j":2,"s":4},{"r":1,"p":9829,"j":2,"s":6},{"r":1,"p":9828,"j":3,"s":4},{"r":1,"p":9829,"j":3,"s":6},{"r":1,"p":9828,"j":4,"s":4},{"r":1,"p":9829,"j":4,"s":6},{"r":1,"p":9828,"j":5,"s":4},{"r":1,"p":9829,"j":5,"s":6}],"judgesSubprograms":[{"r":1,"p":12881,"j":1,"s":2.8},{"r":1,"p":12882,"j":1,"s":1.6},{"r":1,"p":12883,"j":1,"s":1.5},{"r":1,"p":12884,"j":1,"s":1.4},{"r":1,"p":12881,"j":2,"s":4},{"r":1,"p":12882,"j":2,"s":2},{"r":1,"p":12883,"j":2,"s":2},{"r":1,"p":12884,"j":2,"s":2},{"r":1,"p":12881,"j":3,"s":4},{"r":1,"p":12882,"j":3,"s":2},{"r":1,"p":12883,"j":3,"s":2},{"r":1,"p":12884,"j":3,"s":2},{"r":1,"p":12881,"j":4,"s":4},{"r":1,"p":12882,"j":4,"s":2},{"r":1,"p":12883,"j":4,"s":2},{"r":1,"p":12884,"j":4,"s":2},{"r":1,"p":12881,"j":5,"s":4},{"r":1,"p":12882,"j":5,"s":2},{"r":1,"p":12883,"j":5,"s":2},{"r":1,"p":12884,"j":5,"s":2}],"totalPrograms":[{"p":9828,"s":18.8},{"p":9829,"s":28.5}],"avgPrograms":[{"p":9828,"s":4},{"p":9829,"s":6}],"minJudges":[{"p":9828,"j":1},{"p":9829,"j":1}],"maxJudges":[{"p":9828,"j":2},{"p":9829,"j":2}],"total":0,"avg":0,"finalScore":10,"deduction":0},"338464":{"judgesPrograms":[{"r":1,"p":9828,"j":1,"s":3.2},{"r":1,"p":9829,"j":1,"s":3},{"r":1,"p":9828,"j":2,"s":4},{"r":1,"p":9829,"j":2,"s":6},{"r":1,"p":9828,"j":3,"s":4},{"r":1,"p":9829,"j":3,"s":6},{"r":1,"p":9828,"j":4,"s":4},{"r":1,"p":9829,"j":4,"s":6},{"r":1,"p":9828,"j":5,"s":4},{"r":1,"p":9829,"j":5,"s":6}],"judgesSubprograms":[{"r":1,"p":12881,"j":1,"s":3.2},{"r":1,"p":12882,"j":1,"s":1.2},{"r":1,"p":12883,"j":1,"s":1},{"r":1,"p":12884,"j":1,"s":0.8},{"r":1,"p":12881,"j":2,"s":4},{"r":1,"p":12882,"j":2,"s":2},{"r":1,"p":12883,"j":2,"s":2},{"r":1,"p":12884,"j":2,"s":2},{"r":1,"p":12881,"j":3,"s":4},{"r":1,"p":12882,"j":3,"s":2},{"r":1,"p":12883,"j":3,"s":2},{"r":1,"p":12884,"j":3,"s":2},{"r":1,"p":12881,"j":4,"s":4},{"r":1,"p":12882,"j":4,"s":2},{"r":1,"p":12883,"j":4,"s":2},{"r":1,"p":12884,"j":4,"s":2},{"r":1,"p":12881,"j":5,"s":4},{"r":1,"p":12882,"j":5,"s":2},{"r":1,"p":12883,"j":5,"s":2},{"r":1,"p":12884,"j":5,"s":2}],"totalPrograms":[{"p":9828,"s":19.2},{"p":9829,"s":27}],"avgPrograms":[{"p":9828,"s":4},{"p":9829,"s":6}],"minJudges":[{"p":9828,"j":1},{"p":9829,"j":1}],"maxJudges":[{"p":9828,"j":2},{"p":9829,"j":2}],"total":0,"avg":0,"finalScore":10,"deduction":0}},"2":{"338462":{"judgesPrograms":[{"r":2,"p":9828,"j":1,"s":2.8},{"r":2,"p":9829,"j":1,"s":2.6999999999999997},{"r":2,"p":9828,"j":2,"s":4},{"r":2,"p":9829,"j":2,"s":6},{"r":2,"p":9828,"j":3,"s":4},{"r":2,"p":9829,"j":3,"s":6},{"r":2,"p":9828,"j":4,"s":4},{"r":2,"p":9829,"j":4,"s":6},{"r":2,"p":9828,"j":5,"s":4},{"r":2,"p":9829,"j":5,"s":6}],"judgesSubprograms":[{"r":2,"p":12881,"j":1,"s":2.8},{"r":2,"p":12882,"j":1,"s":1.2},{"r":2,"p":12883,"j":1,"s":0.8999999999999999},{"r":2,"p":12884,"j":1,"s":0.6000000000000001},{"r":2,"p":12881,"j":2,"s":4},{"r":2,"p":12882,"j":2,"s":2},{"r":2,"p":12883,"j":2,"s":2},{"r":2,"p":12884,"j":2,"s":2},{"r":2,"p":12881,"j":3,"s":4},{"r":2,"p":12882,"j":3,"s":2},{"r":2,"p":12883,"j":3,"s":2},{"r":2,"p":12884,"j":3,"s":2},{"r":2,"p":12881,"j":4,"s":4},{"r":2,"p":12882,"j":4,"s":2},{"r":2,"p":12883,"j":4,"s":2},{"r":2,"p":12884,"j":4,"s":2},{"r":2,"p":12881,"j":5,"s":4},{"r":2,"p":12882,"j":5,"s":2},{"r":2,"p":12883,"j":5,"s":2},{"r":2,"p":12884,"j":5,"s":2}],"totalPrograms":[{"p":9828,"s":18.8},{"p":9829,"s":26.7}],"avgPrograms":[{"p":9828,"s":4},{"p":9829,"s":6}],"minJudges":[{"p":9828,"j":1},{"p":9829,"j":1}],"maxJudges":[{"p":9828,"j":2},{"p":9829,"j":2}],"total":0,"avg":0,"finalScore":10,"deduction":0},"338464":{"judgesPrograms":[{"r":2,"p":9828,"j":1,"s":2.9},{"r":2,"p":9829,"j":1,"s":3},{"r":2,"p":9828,"j":2,"s":4},{"r":2,"p":9829,"j":2,"s":6},{"r":2,"p":9828,"j":3,"s":4},{"r":2,"p":9829,"j":3,"s":6},{"r":2,"p":9828,"j":4,"s":4},{"r":2,"p":9829,"j":4,"s":6},{"r":2,"p":9828,"j":5,"s":4},{"r":2,"p":9829,"j":5,"s":6}],"judgesSubprograms":[{"r":2,"p":12881,"j":1,"s":2.9},{"r":2,"p":12882,"j":1,"s":1.3},{"r":2,"p":12883,"j":1,"s":1},{"r":2,"p":12884,"j":1,"s":0.7},{"r":2,"p":12881,"j":2,"s":4},{"r":2,"p":12882,"j":2,"s":2},{"r":2,"p":12883,"j":2,"s":2},{"r":2,"p":12884,"j":2,"s":2},{"r":2,"p":12881,"j":3,"s":4},{"r":2,"p":12882,"j":3,"s":2},{"r":2,"p":12883,"j":3,"s":2},{"r":2,"p":12884,"j":3,"s":2},{"r":2,"p":12881,"j":4,"s":4},{"r":2,"p":12882,"j":4,"s":2},{"r":2,"p":12883,"j":4,"s":2},{"r":2,"p":12884,"j":4,"s":2},{"r":2,"p":12881,"j":5,"s":4},{"r":2,"p":12882,"j":5,"s":2},{"r":2,"p":12883,"j":5,"s":2},{"r":2,"p":12884,"j":5,"s":2}],"totalPrograms":[{"p":9828,"s":18.9},{"p":9829,"s":27}],"avgPrograms":[{"p":9828,"s":4},{"p":9829,"s":6}],"minJudges":[{"p":9828,"j":1},{"p":9829,"j":1}],"maxJudges":[{"p":9828,"j":2},{"p":9829,"j":2}],"total":0,"avg":0,"finalScore":10,"deduction":0}},"3":{}}},"judgesSettings":[{"id":1,"isConnected":false,"token":"01knwdxcrxcrxkgz3rh0hvttad"},{"id":2,"isConnected":false,"token":"01knwdxcrywtbsqbjfm206133p"},{"id":3,"isConnected":false,"token":"01knwdxcrz6ww70zbyn06jf0zv"},{"id":4,"isConnected":false,"token":"01knwdxcrzfjwrgp7q3kw6qcst"},{"id":5,"isConnected":false,"token":"01knwdxcs0jj9zaw3653wx5d7y"}],"tv_type":1,"sportName":"Taekwondo","nextCompetitions":[{"id":5336196,"event_id":11534,"division_id":15113,"group_id":null,"category_id":831904,"sp1_id":338460,"sp2_id":338463,"leftId":5336194,"rightId":5336195,"loseLeftId":0,"loseRightId":0,"winner_id":0,"score_one":0,"score_two":0,"priority_score":0,"winner_n":0,"is_final":0,"serial":3,"win_type_id":1,"number":2,"type":0,"court":1,"warnings_one":0,"warnings_two":0,"currentRoundTime":"00:00","currentRoundNumber":1,"currentRoundType":1,"currentRoundStatus":0,"lastStartTime":"2026-04-10T22:37:08.000Z","is_finished":0,"faultsOne":0,"faultsTwo":0,"is_active":0,"day":1,"set_score_time":0,"place":2,"area_id":16479,"is_single":0,"is_team":0,"settings_id":34807,"start_time":"00:00","canceled":0,"disq1":0,"disq2":0,"is_fake":0,"stage_id":0,"group_number":0,"stage_number":0,"spent_time":0,"pool_id":38689,"seed1":0,"seed2":0,"locked":0,"euid":0,"rounds":null,"round":0,"custom_start_time":-1,"details":null,"tiebreak":0,"user1":{"user":{"id":338460,"name":"Gregory","surname":"Turner","link":null,"image_url":"","gender":1,"birthdate":"1985-01-01"},"academy":"","org":{"image_url":"","title":"Core Sports","link":null,"id":4868,"country_code":"AU"},"metadata":null},"user2":{"user":{"id":338463,"name":"Steven","surname":"Silverton","link":null,"image_url":"","gender":1,"birthdate":"1985-01-01"},"academy":"","org":{"image_url":"","title":"Phoenix Sports","link":null,"id":4803,"country_code":"ZA"},"metadata":null},"color1":"blue","color2":"red"},{"id":5336200,"event_id":11534,"division_id":15113,"group_id":null,"category_id":831904,"sp1_id":338465,"sp2_id":338466,"leftId":5336198,"rightId":5336199,"loseLeftId":0,"loseRightId":0,"winner_id":0,"score_one":0,"score_two":0,"priority_score":0,"winner_n":0,"is_final":0,"serial":3,"win_type_id":1,"number":3,"type":0,"court":1,"warnings_one":0,"warnings_two":0,"currentRoundTime":"00:00","currentRoundNumber":1,"currentRoundType":1,"currentRoundStatus":0,"lastStartTime":"2026-04-10T22:37:08.000Z","is_finished":0,"faultsOne":0,"faultsTwo":0,"is_active":0,"day":1,"set_score_time":0,"place":2,"area_id":16479,"is_single":0,"is_team":0,"settings_id":34807,"start_time":"00:00","canceled":0,"disq1":0,"disq2":0,"is_fake":0,"stage_id":0,"group_number":0,"stage_number":0,"spent_time":0,"pool_id":38689,"seed1":0,"seed2":0,"locked":0,"euid":0,"rounds":null,"round":0,"custom_start_time":-1,"details":null,"tiebreak":0,"user1":{"user":{"id":338465,"name":"William","surname":"Martin","link":null,"image_url":"","gender":1,"birthdate":"1985-01-01"},"academy":"","org":{"image_url":"","title":"Patriot Athletics","link":null,"id":4183,"country_code":"ZA"},"metadata":null},"user2":{"user":{"id":338466,"name":"Gary","surname":"Goldenberg","link":null,"image_url":"","gender":1,"birthdate":"1985-01-01"},"academy":"","org":{"image_url":"","title":"Victory Sports","link":null,"id":4161,"country_code":"BR"},"metadata":null},"color1":"blue","color2":"red"},{"id":5336203,"event_id":11534,"division_id":15113,"group_id":null,"category_id":831904,"sp1_id":338461,"sp2_id":338459,"leftId":5336201,"rightId":5336202,"loseLeftId":0,"loseRightId":0,"winner_id":0,"score_one":0,"score_two":0,"priority_score":0,"winner_n":0,"is_final":0,"serial":3,"win_type_id":1,"number":4,"type":0,"court":1,"warnings_one":0,"warnings_two":0,"currentRoundTime":"00:00","currentRoundNumber":1,"currentRoundType":1,"currentRoundStatus":0,"lastStartTime":"2026-04-10T22:37:08.000Z","is_finished":0,"faultsOne":0,"faultsTwo":0,"is_active":0,"day":1,"set_score_time":0,"place":2,"area_id":16479,"is_single":0,"is_team":0,"settings_id":34807,"start_time":"00:00","canceled":0,"disq1":0,"disq2":0,"is_fake":0,"stage_id":0,"group_number":0,"stage_number":0,"spent_time":0,"pool_id":38689,"seed1":0,"seed2":0,"locked":0,"euid":0,"rounds":null,"round":0,"custom_start_time":-1,"details":null,"tiebreak":0,"user1":{"user":{"id":338461,"name":"Justin","surname":"Walker","link":null,"image_url":"","gender":1,"birthdate":"1985-01-01"},"academy":"","org":{"image_url":"","title":"Core Sports","link":null,"id":4868,"country_code":"AU"},"metadata":null},"user2":{"user":{"id":338459,"name":"Daniel","surname":"Robinson","link":null,"image_url":"","gender":1,"birthdate":"1985-01-01"},"academy":"","org":{"image_url":"","title":"Thunder Sports","link":null,"id":4864,"country_code":"BR"},"metadata":null},"color1":"blue","color2":"red"}],"isGrandFinal":false,"sport_id":1,"nextMatchId":5336196,"prevMatchId":0,"judges":[],"timerData":{"round_id":2,"timeLeft":0,"tempTimeLeft":0,"isPause":true,"isRest":false,"isRound":true,"isDoctor1":false,"isDoctor2":false,"doctorTime1":0,"doctorTime2":0,"dRoundTime":90000,"dRestTime":0,"isExtra":false},"customTimersData":[],"nestedPairs":[],"categoryFinished":false}},"fetchId":"af629644-3140-475d-b5fe-79a716401d2a","appv":"2.0.92"}]

"""