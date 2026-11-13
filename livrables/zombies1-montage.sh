set -e
FONT=/usr/share/fonts/opentype/inter/InterDisplay-Bold.otf
B="fontfile=$FONT:fontcolor=white:borderw=7:bordercolor=black:fontsize=70:line_spacing=12:x=(w-text_w)/2:y=230"
K="scale=-2:1920:flags=lanczos,crop=1080:1920,fps=30,setsar=1,format=yuv420p"
P="scale=-2:1920:flags=lanczos,crop=1080:1920,unsharp=5:5:0.4,fps=30,setsar=1,format=yuv420p"
k=kaggle; h=hf
ffmpeg -v error -y -i $k/plan1-salon-g42.mp4 -i $k/plan2-voyant-g42.mp4 -i $k/plan3-chat-g42.mp4 -i $h/zombies11.mp4 -i $h/zombies1b1.mp4 -i $k/plan6-cooper-g42.mp4 -i $h/zombies14.mp4 -i $h/zombies13.mp4 -i $h/zombies12.mp4 -i $k/plan10-regards-g42.mp4 -i $k/plan11-encercles-g42.mp4 -i $k/plan12-noir-g42.mp4 -filter_complex "\
[0:v]trim=end_frame=32,setpts=PTS-STARTPTS,$K,drawtext=$B:textfile=t1.txt[a1];\
[1:v]trim=end_frame=48,setpts=PTS-STARTPTS,$K,drawtext=$B:textfile=t4.txt[a2];\
[2:v]trim=end_frame=48,setpts=PTS-STARTPTS,$K[a3];\
[3:v]trim=end_frame=49,setpts=PTS-STARTPTS,$P[a4];\
[4:v]trim=end_frame=49,setpts=PTS-STARTPTS,$P[a5];\
[5:v]trim=end_frame=60,setpts=PTS-STARTPTS,$K[a6];\
[6:v]trim=end_frame=44,setpts=PTS-STARTPTS,$P,drawtext=$B:textfile=t7.txt[a7];\
[7:v]trim=end_frame=32,setpts=PTS-STARTPTS,$P[a8];\
[8:v]trim=end_frame=40,setpts=PTS-STARTPTS,$P[a9];\
[9:v]trim=end_frame=48,setpts=PTS-STARTPTS,$K[a10];\
[10:v]trim=end_frame=72,setpts=PTS-STARTPTS,$K[a11];\
[11:v]trim=end_frame=60,setpts=PTS-STARTPTS,$K,drawtext=$B:textfile=t12.txt[a12];\
[a1][a2][a3][a5][a6][a4][a7][a8][a9][a10][a11][a12]concat=n=12:v=1:a=0[v]" -map "[v]" -c:v libx264 -crf 27 -preset slow -movflags +faststart zombies1-muet.mp4
d=$(ffprobe -v error -show_entries format=duration -of csv=p=0 zombies1-muet.mp4)
ffmpeg -v error -y -i zombies1-muet.mp4 -i /mnt/project-files/sons/happyukulele.mp3 -filter_complex "[1:a]atrim=0.8,asetpts=PTS-STARTPTS,atrim=0:$d,afade=t=out:st=$(echo "$d-1"|bc):d=1[a]" -map 0:v -map "[a]" -c:v copy -c:a aac -b:a 160k -shortest zombies1-youtube.mp4
echo $d
