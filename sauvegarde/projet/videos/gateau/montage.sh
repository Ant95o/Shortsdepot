set -e
FONT=/usr/share/fonts/opentype/inter/InterDisplay-Bold.otf
B="fontfile=$FONT:fontcolor=white:borderw=7:bordercolor=black:fontsize=70:line_spacing=12:x=(w-text_w)/2:y=230"
K="scale=-2:1920:flags=lanczos,crop=1080:1920,fps=30,setsar=1,format=yuv420p"
ffmpeg -v error -y -i plan1-gateau-g42.mp4 -i plan2-repere-g42.mp4 -i plan3-innocent-g42.mp4 -i plan4-chat-g42.mp4 -i plan5-porte-g42.mp4 -i plan7-pattes-g42.mp4 -i plan8-leche-g42.mp4 -i plan9-porte-g42.mp4 -i plan10-zoom.mp4 -i plan11-coupable-g42.mp4 -i plan12-chat-g42.mp4 -filter_complex "\
[0:v]trim=end_frame=48,setpts=PTS-STARTPTS,$K,drawtext=$B:textfile=t1.txt[a1];\
[1:v]trim=end_frame=48,setpts=PTS-STARTPTS,$K[a2];\
[2:v]trim=end_frame=48,setpts=PTS-STARTPTS,$K,drawtext=$B:textfile=t3.txt[a3];\
[3:v]trim=end_frame=48,setpts=PTS-STARTPTS,$K[a4];\
[4:v]trim=end_frame=72,setpts=PTS-STARTPTS,$K[a5];\
[5:v]trim=end_frame=66,setpts=PTS-STARTPTS,$K,drawtext=$B:textfile=t7.txt[a7];\
[6:v]trim=end_frame=60,setpts=PTS-STARTPTS,$K[a8];\
[7:v]trim=end_frame=40,setpts=PTS-STARTPTS,$K,drawtext=$B:textfile=t9.txt[a9];\
[8:v]trim=end_frame=66,setpts=PTS-STARTPTS,$K,drawtext=$B:textfile=t10.txt[a10];\
[9:v]trim=end_frame=60,setpts=PTS-STARTPTS,$K,drawtext=$B:textfile=t11.txt[a11];\
[10:v]trim=end_frame=72,setpts=PTS-STARTPTS,$K,drawtext=$B:textfile=t12.txt[a12];\
[a1][a2][a3][a4][a5][a7][a8][a9][a10][a11][a12]concat=n=11:v=1:a=0[v]" -map "[v]" -c:v libx264 -crf 27 -preset slow -movflags +faststart gateau-muet.mp4
d=$(ffprobe -v error -show_entries format=duration -of csv=p=0 gateau-muet.mp4)
ffmpeg -v error -y -i gateau-muet.mp4 -i /mnt/project-files/sons/happyukulele.mp3 -filter_complex "[1:a]atrim=0.8,asetpts=PTS-STARTPTS,atrim=0:$d,afade=t=out:st=$(echo "$d-1"|bc):d=1[a]" -map 0:v -map "[a]" -c:v copy -c:a aac -b:a 160k -shortest gateau-youtube.mp4
echo $d
