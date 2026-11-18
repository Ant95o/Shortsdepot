set -e
FONT=/usr/share/fonts/opentype/inter/InterDisplay-Bold.otf
B="fontfile=$FONT:fontcolor=white:borderw=7:bordercolor=black:fontsize=70:line_spacing=12:x=(w-text_w)/2:y=230"
P="scale=-2:1920:flags=lanczos,crop=1080:1920,unsharp=5:5:0.4,fps=30,setsar=1,format=yuv420p"
K="scale=-2:1920:flags=lanczos,crop=1080:1920,fps=30,setsar=1,format=yuv420p"
ffmpeg -v error -y -i clip1.mp4 -i clip2.mp4 -i clip3.mp4 -i clip4.mp4 -i clip5.mp4 -i clip6.mp4 -i clip7.mp4 \
 -i plan8-saute-g42.mp4 -i plan9-coussin-g42.mp4 -i plan10-plante-g42.mp4 -i plan11-terre-g42.mp4 -i plan12-figes-g42.mp4 -i plan13-innocents-g42.mp4 -filter_complex "\
[0:v]trim=end_frame=32,setpts=PTS-STARTPTS,$P,drawtext=$B:textfile=t1.txt[a1];\
[1:v]trim=end_frame=36,setpts=PTS-STARTPTS,$P[a2];\
[2:v]trim=end_frame=36,setpts=PTS-STARTPTS,$P[a3];\
[3:v]trim=end_frame=40,setpts=PTS-STARTPTS,$P,drawtext=$B:textfile=t4.txt[a4];\
[4:v]trim=end_frame=36,setpts=PTS-STARTPTS,$P[a5];\
[5:v]trim=end_frame=36,setpts=PTS-STARTPTS,$P[a6];\
[6:v]trim=end_frame=40,setpts=PTS-STARTPTS,$P[a7];\
[7:v]trim=end_frame=38,setpts=PTS-STARTPTS,$K[a8];\
[8:v]trim=end_frame=50,setpts=PTS-STARTPTS,$K[a9];\
[9:v]trim=end_frame=38,setpts=PTS-STARTPTS,$K[a10];\
[10:v]trim=end_frame=44,setpts=PTS-STARTPTS,$K[a11];\
[11:v]trim=end_frame=42,setpts=PTS-STARTPTS,$K,drawtext=$B:textfile=t12.txt[a12];\
[12:v]trim=end_frame=66,setpts=PTS-STARTPTS,$K,drawtext=$B:textfile=t13.txt[a13];\
[a1][a2][a3][a4][a5][a6][a7][a8][a9][a10][a11][a12][a13]concat=n=13:v=1:a=0[v]" -map "[v]" -c:v libx264 -crf 20 -preset slow -movflags +faststart housewife-muet.mp4
d=$(ffprobe -v error -show_entries format=duration -of csv=p=0 housewife-muet.mp4)
ffmpeg -v error -y -i housewife-muet.mp4 -i /mnt/project-files/sons/happyukulele.mp3 -filter_complex "[1:a]atrim=0.8,asetpts=PTS-STARTPTS,atrim=0:$d,afade=t=out:st=$(echo "$d-1"|bc):d=1[a]" -map 0:v -map "[a]" -c:v copy -c:a aac -b:a 160k -shortest housewife-youtube.mp4
echo $d
