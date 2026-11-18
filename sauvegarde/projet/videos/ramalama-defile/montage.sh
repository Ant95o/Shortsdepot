set -e
FONT=/usr/share/fonts/opentype/inter/InterDisplay-Bold.otf
T="fontfile=$FONT:fontcolor=white:borderw=7:bordercolor=black:fontsize=72:line_spacing=12:x=(w-text_w)/2"
P="setpts=PTS-STARTPTS,crop=1080:1920,unsharp=5:5:0.3,fps=30,setsar=1,format=yuv420p"
ffmpeg -v error -y -i plan1-chat.mp4 -i plan2-corgi.mp4 -i plan3-tortue.mp4 -filter_complex "
[0:v]trim=end_frame=100,$P,drawtext=$T:y=230:textfile=t0.txt:enable='lt(t,2)',drawtext=$T:y=1500:textfile=t1.txt:enable='gte(t,2)'[a];
[1:v]trim=end_frame=90,$P,drawtext=$T:y=1500:textfile=t2.txt[b];
[2:v]trim=end_frame=90,$P,drawtext=$T:y=1450:textfile=t3.txt:enable='gte(t,0.5)'[c];
[a][b][c]concat=n=3:v=1:a=0[v]" -map "[v]" -c:v libx264 -crf 21 -preset slow -movflags +faststart ramalama-muet.mp4
ffprobe -v error -show_entries format=duration -of csv=p=0 ramalama-muet.mp4
