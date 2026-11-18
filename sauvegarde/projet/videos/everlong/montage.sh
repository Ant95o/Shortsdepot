set -e
FONT=/usr/share/fonts/opentype/inter/InterDisplay-Bold.otf
B="fontfile=$FONT:fontcolor=white:borderw=7:bordercolor=black:fontsize=70:line_spacing=12:x=(w-text_w)/2:y=230"
P="scale=-2:1920:flags=lanczos,crop=1080:1920,unsharp=5:5:0.4,fps=30,setsar=1,format=yuv420p"
K="scale=-2:1920:flags=lanczos,crop=1080:1920,fps=30,setsar=1,format=yuv420p"
ffmpeg -v error -y -i plan1-assis-g42.mp4 -i hf1.mp4 -i hf2.mp4 -i plan4-fier-g42.mp4 -i plan5-branche-g42.mp4 -i plan6-traine-g42.mp4 -i plan7-coince-g42.mp4 -i plan8-tire-g42.mp4 -i plan9-chat-g42.mp4 -i plan10-fin-g42.mp4 -filter_complex "\
[0:v]trim=end_frame=48,setpts=PTS-STARTPTS,$K,drawtext=$B:textfile=t1.txt[a1];\
[1:v]trim=end_frame=40,setpts=PTS-STARTPTS,$P[a2];\
[2:v]trim=end_frame=49,setpts=PTS-STARTPTS,$P,drawtext=$B:textfile=t3.txt[a3];\
[3:v]trim=end_frame=48,setpts=PTS-STARTPTS,$K[a4];\
[4:v]trim=end_frame=48,setpts=PTS-STARTPTS,$K,drawtext=$B:textfile=t5.txt[a5];\
[5:v]trim=end_frame=72,setpts=PTS-STARTPTS,$K[a6];\
[6:v]trim=end_frame=60,setpts=PTS-STARTPTS,$K,drawtext=$B:textfile=t7.txt[a7];\
[7:v]trim=end_frame=72,setpts=PTS-STARTPTS,$K[a8];\
[8:v]trim=end_frame=60,setpts=PTS-STARTPTS,$K,drawtext=$B:textfile=t9.txt[a9];\
[9:v]trim=end_frame=72,setpts=PTS-STARTPTS,$K,drawtext=$B:textfile=t10.txt[a10];\
[a1][a2][a3][a4][a5][a6][a7][a8][a9][a10]concat=n=10:v=1:a=0[v]" -map "[v]" -c:v libx264 -crf 20 -preset slow -movflags +faststart everlong-muet.mp4
d=$(ffprobe -v error -show_entries format=duration -of csv=p=0 everlong-muet.mp4)
ffmpeg -v error -y -i everlong-muet.mp4 -i /mnt/project-files/sons/happyukulele.mp3 -filter_complex "[1:a]atrim=0.8,asetpts=PTS-STARTPTS,atrim=0:$d,afade=t=out:st=$(echo "$d-1"|bc):d=1[a]" -map 0:v -map "[a]" -c:v libx264 -crf 24 -preset slow -c:a aac -b:a 160k -shortest everlong-youtube.mp4
echo $d
