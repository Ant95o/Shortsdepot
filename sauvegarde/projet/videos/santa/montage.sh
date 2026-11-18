set -e
FONT=/usr/share/fonts/opentype/inter/InterDisplay-Bold.otf
B="fontfile=$FONT:fontcolor=white:borderw=7:bordercolor=black:fontsize=70:line_spacing=12:x=(w-text_w)/2:y=230"
K="scale=-2:1920:flags=lanczos,crop=1080:1920,fps=30,setsar=1,format=yuv420p"
P="scale=-2:1920:flags=lanczos,crop=1080:1920,unsharp=5:5:0.4,fps=30,setsar=1,format=yuv420p"
k=kaggle; h=hf
ffmpeg -v error -y -i $k/plan1-salon-g42.mp4 -i $h/santa5.mp4 -i $k/plan3-dessin-g42.mp4 -i $h/santa1.mp4 -i $h/santa2.mp4 -i $k/plan6-os-g42.mp4 -i $h/santa4.mp4 -i $k/plan10-oeil-g42.mp4 -i $k/plan11-cadeaux-g42.mp4 -i $h/santa3.mp4 -filter_complex "\
[0:v]trim=end_frame=60,setpts=PTS-STARTPTS,$K,drawtext=$B:textfile=t1.txt[a1];\
[1:v]trim=end_frame=40,setpts=PTS-STARTPTS,$P,drawtext=$B:textfile=t2.txt[a2];\
[2:v]trim=end_frame=48,setpts=PTS-STARTPTS,$K[a3];\
[3:v]trim=end_frame=40,setpts=PTS-STARTPTS,$P[a4];\
[4:v]trim=end_frame=49,setpts=PTS-STARTPTS,$P,drawtext=$B:textfile=t5.txt[a5];\
[5:v]trim=end_frame=45,setpts=PTS-STARTPTS,$K[a6];\
[6:v]trim=end_frame=30,setpts=PTS-STARTPTS,$P,drawtext=$B:textfile=t9.txt[a9];\
[7:v]trim=end_frame=48,setpts=PTS-STARTPTS,$K[a10];\
[8:v]trim=end_frame=45,setpts=PTS-STARTPTS,$K,drawtext=$B:textfile=t11.txt[a11];\
[9:v]trim=end_frame=30,setpts=PTS-STARTPTS,$P[a12];\
[a1][a2][a3][a4][a5][a6][a9][a10][a11][a12]concat=n=10:v=1:a=0[v]" -map "[v]" -c:v libx264 -crf 27 -preset slow -movflags +faststart santa-muet.mp4
d=$(ffprobe -v error -show_entries format=duration -of csv=p=0 santa-muet.mp4)
ffmpeg -v error -y -i santa-muet.mp4 -i /mnt/project-files/sons/happyukulele.mp3 -filter_complex "[1:a]atrim=0.8,asetpts=PTS-STARTPTS,atrim=0:$d,afade=t=out:st=$(echo "$d-1"|bc):d=1[a]" -map 0:v -map "[a]" -c:v copy -c:a aac -b:a 160k -shortest santa-youtube.mp4
echo $d
