set -e
FONT=/usr/share/fonts/opentype/inter/InterDisplay-Bold.otf
B="fontfile=$FONT:fontcolor=white:borderw=7:bordercolor=black:fontsize=68:line_spacing=12:x=(w-text_w)/2"
T="$B:y=230"; L="$B:y=1480"
P="setpts=PTS-STARTPTS,crop=1080:1920,unsharp=5:5:0.3,fps=30,setsar=1,format=yuv420p"
ffmpeg -v error -y -i plan1-arrive-g42.mp4 -i plan2-creuse-g42.mp4 -i plan3-recouvre-v2-g42.mp4 -i plan4-teckel-voit-g42.mp4 -i plan5-perdu-g42.mp4 -i plan6-creuse-fou-g42.mp4 -i plan7-trous-g42.mp4 -i plan8-teckel-ronge-g42.mp4 -filter_complex "
[0:v]trim=end_frame=62,$P,drawtext=$T:textfile=t1.txt[a];
[1:v]trim=end_frame=56,$P[b];
[2:v]trim=end_frame=44,$P,drawtext=$T:textfile=t3.txt[c];
[3:v]trim=end_frame=62,$P,drawtext=$L:textfile=t4.txt[d];
[4:v]trim=end_frame=55,$P,drawtext=$T:textfile=t5.txt[e];
[5:v]trim=end_frame=42,$P,drawtext=$T:textfile=t6.txt[f];
[6:v]trim=end_frame=70,$P[g];
[7:v]trim=end_frame=84,$P,drawtext=$T:textfile=t8.txt[h];
[a][b][c][d][e][f][g][h]concat=n=8:v=1:a=0[v]" -map "[v]" -c:v libx264 -crf 27 -maxrate 6M -bufsize 12M -preset slow -movflags +faststart os-muet.mp4
d=$(ffprobe -v error -show_entries format=duration -of csv=p=0 os-muet.mp4)
ffmpeg -v error -y -i os-muet.mp4 -i /mnt/project-files/sons/happyukulele.mp3 -filter_complex "[1:a]atrim=0.8,asetpts=PTS-STARTPTS,atrim=0:$d,afade=t=out:st=$(echo "$d-1.2"|bc):d=1.2[a]" -map 0:v -map "[a]" -c:v copy -c:a aac -b:a 160k -shortest os-youtube.mp4
echo $d
