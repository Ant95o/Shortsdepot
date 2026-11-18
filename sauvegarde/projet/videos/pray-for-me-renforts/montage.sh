set -e
FONT=/usr/share/fonts/opentype/inter/InterDisplay-Bold.otf
T="fontfile=$FONT:fontcolor=white:borderw=7:bordercolor=black:fontsize=72:line_spacing=12:x=(w-text_w)/2"
CX=626; CY=1262
# porche vide (image 5 du plan Kaggle), marche au ralenti x2,5 (images 66-120)
ffmpeg -v error -y -i plan1.mp4 -vf "select=eq(n\,5),crop=1080:1920" -frames:v 1 vide.png
[ -f ralenti.mp4 ] || ffmpeg -v error -y -i plan1.mp4 -vf "trim=start_frame=66:end_frame=121,setpts=2.5*(PTS-STARTPTS),minterpolate=fps=32:mi_mode=mci:mc_mode=aobmc:vsbmc=1,crop=1080:1920,unsharp=5:5:0.4" -c:v libx264 -crf 14 -preset fast ralenti.mp4
ffmpeg -v error -y -loop 1 -t 1.8 -framerate 32 -i vide.png -i ralenti.mp4 -loop 1 -framerate 32 -i vide.png -loop 1 -i halo.png -loop 1 -t 1.8 -framerate 32 -i vide.png -filter_complex "
[0:v]format=yuv420p,setsar=1,drawtext=$T:y=280:textfile=t1.txt[a];
[1:v]setpts=PTS-STARTPTS,fps=32,format=yuv420p,setsar=1,drawtext=$T:y=280:textfile=t2.txt[b];
[3:v]scale=380:380,format=rgba[h];
[2:v]trim=end_frame=32,setpts=PTS-STARTPTS[zs];
[zs][h]overlay=x=$CX-190:y=$CY-250:enable='gte(n,4)*not(between(n,11,12))':shortest=1,
 zoompan=z='if(lt(on,8),1+on*0.2,2.6)':x='max(0,min(iw-iw/zoom,$CX-iw/zoom/2+if(gte(on,8),10*sin(on*1.7),0)))':y='max(0,min(ih-ih/zoom,$CY-ih/zoom/2+if(gte(on,8),10*cos(on*2.3),0)))':d=1:s=1080x1920:fps=32,
 drawbox=c=white@0.8:t=fill:enable='between(n,8,9)',trim=end_frame=32,setpts=PTS-STARTPTS,format=yuv420p,setsar=1[z];
[4:v]format=yuv420p,setsar=1,drawtext=$T:y=280:textfile=t3.txt[e];
[a][b][z][e]concat=n=4:v=1:a=0,format=yuv420p[v]" -map "[v]" -c:v libx264 -crf 17 -preset medium -r 32 muet.mp4
DUR=$(ffprobe -v error -show_entries format=duration -of csv=p=0 muet.mp4); RD=$(ffprobe -v error -show_entries format=duration -of csv=p=0 ralenti.mp4); echo dur $DUR ralenti $RD
# son : coeur pendant la marche, tonnerre sur le flash (début zoom + 0,25 s)
A=/mnt/project-files/sons
FL=$(python3 -c "print(1.8+$RD+0.25)")
ffmpeg -v error -y -i $A/coeur1.ogg -af "atrim=start=0.82,asetpts=PTS-STARTPTS,atrim=0:$RD,afade=t=out:st=$(python3 -c "print($RD-0.2)"):d=0.2,adelay=1800|1800,apad=whole_dur=$DUR,aresample=48000" -ac 2 c.wav
ffmpeg -v error -y -i $A/tonnerre0.ogg -af "atrim=start=10.75,asetpts=PTS-STARTPTS,atrim=0:2.6,afade=t=out:st=1.8:d=0.8,adelay=$(python3 -c "print(int(($FL-0.05)*1000))")|$(python3 -c "print(int(($FL-0.05)*1000))"),apad=whole_dur=$DUR,aresample=48000" -ac 2 tn.wav
ffmpeg -v error -y -i c.wav -i tn.wav -filter_complex "[0][1]amix=inputs=2:normalize=0,loudnorm=I=-14:TP=-1.5,aresample=48000[a]" -map "[a]" mix.wav
ffmpeg -v error -y -i muet.mp4 -i mix.wav -map 0:v -map 1:a -c:v copy -c:a aac -b:a 192k son.mp4
