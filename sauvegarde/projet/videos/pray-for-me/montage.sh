set -e
FONT=/usr/share/fonts/opentype/inter/InterDisplay-Bold.otf
B="fontfile=$FONT:fontcolor=white:borderw=7:bordercolor=black:fontsize=70:line_spacing=12:x=(w-text_w)/2:y=230"
K="scale=-2:1920:flags=lanczos,crop=1080:1920,fps=30,setsar=1,format=yuv420p"
P="scale=-2:1920:flags=lanczos,crop=1080:1920,unsharp=5:5:0.4,fps=30,setsar=1,format=yuv420p"
k=kaggle; h=hf
ffmpeg -v error -y -i $k/plan1-croquette-g42.mp4 -i $k/plan2-chat-g42.mp4 -i $k/plan3-cooper-g42.mp4 -i $h/plan4.mp4 -i $h/plan5.mp4 -i $k/plan6-yeux-cooper-g42.mp4 -i $k/plan7-yeux-chat-g42.mp4 -i $k/plan8-face-g42.mp4 -i $h/plan9.mp4 -i $h/plan10.mp4 -i $k/plan11-frigo-g42.mp4 -i $k/plan12-defaite-g42.mp4 -filter_complex "\
[0:v]trim=end_frame=48,setpts=PTS-STARTPTS,$K,drawtext=$B:textfile=t1.txt[a1];\
[1:v]trim=end_frame=48,setpts=PTS-STARTPTS,$K[a2];\
[2:v]trim=end_frame=48,setpts=PTS-STARTPTS,$K,drawtext=$B:textfile=t3.txt[a3];\
[3:v]trim=end_frame=40,setpts=1.3*(PTS-STARTPTS),$P[a4];\
[4:v]trim=end_frame=40,setpts=1.3*(PTS-STARTPTS),$P[a5];\
[5:v]trim=end_frame=50,setpts=PTS-STARTPTS,$K[a6];\
[6:v]trim=end_frame=50,setpts=PTS-STARTPTS,$K[a7];\
[7:v]trim=end_frame=48,setpts=PTS-STARTPTS,$K[a8];\
[8:v]trim=end_frame=36,setpts=PTS-STARTPTS,$P[a9];\
[9:v]trim=end_frame=16,setpts=1.5*(PTS-STARTPTS),$P[a10];\
[10:v]trim=end_frame=44,setpts=PTS-STARTPTS,$K,drawtext=$B:textfile=t11.txt[a11];\
[11:v]trim=end_frame=60,setpts=PTS-STARTPTS,$K[a12];\
[a1][a2][a3][a4][a5][a6][a7][a8][a9][a10][a11][a12]concat=n=12:v=1:a=0[v]" -map "[v]" -c:v libx264 -crf 27 -preset slow -movflags +faststart pray-muet.mp4
d=$(ffprobe -v error -show_entries format=duration -of csv=p=0 pray-muet.mp4)
ffmpeg -v error -y -i pray-muet.mp4 -i /mnt/project-files/sons/happyukulele.mp3 -filter_complex "[1:a]atrim=0.8,asetpts=PTS-STARTPTS,atrim=0:$d,afade=t=out:st=$(echo "$d-1"|bc):d=1[a]" -map 0:v -map "[a]" -c:v copy -c:a aac -b:a 160k -shortest pray-youtube.mp4
echo $d
