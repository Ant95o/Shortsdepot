set -e
FONT=/usr/share/fonts/opentype/inter/InterDisplay-Bold.otf
B="fontfile=$FONT:fontcolor=white:borderw=7:bordercolor=black:fontsize=70:line_spacing=12:x=(w-text_w)/2"
P="scale=-2:1920:flags=lanczos,crop=1080:1920,unsharp=5:5:0.4,fps=30,setsar=1,format=yuv420p"
ffmpeg -v error -y -i kidman1.mp4 -i kidman2.mp4 -i kidman3.mp4 -i kidman4.mp4 -filter_complex "\
[0:v]trim=end_frame=49,setpts=PTS-STARTPTS,$P,drawtext=$B:y=230:textfile=t1.txt[a];\
[1:v]trim=end_frame=42,setpts=PTS-STARTPTS,$P[b];\
[2:v]trim=end_frame=49,setpts=PTS-STARTPTS,$P,drawtext=$B:y=230:textfile=t3.txt:enable='gte(t,0.5)'[c];\
[3:v]trim=end_frame=49,setpts=PTS-STARTPTS,$P[d];\
[a][b][c][d]concat=n=4:v=1:a=0[v]" -map "[v]" -c:v libx264 -crf 20 -preset slow -movflags +faststart kidman-muet.mp4
d=$(ffprobe -v error -show_entries format=duration -of csv=p=0 kidman-muet.mp4)
ffmpeg -v error -y -i kidman-muet.mp4 -i /mnt/project-files/sons/happyukulele.mp3 -filter_complex "[1:a]atrim=0.8,asetpts=PTS-STARTPTS,atrim=0:$d,afade=t=out:st=$(echo "$d-1"|bc):d=1[a]" -map 0:v -map "[a]" -c:v copy -c:a aac -b:a 160k -shortest kidman-youtube.mp4
echo $d
