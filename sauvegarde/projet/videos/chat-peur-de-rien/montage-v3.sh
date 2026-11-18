set -e
FONT=/usr/share/fonts/opentype/inter/InterDisplay-Bold.otf
T="fontfile=$FONT:fontcolor=white:borderw=7:bordercolor=black:fontsize=78:x=(w-text_w)/2"
TC=2.1875; CX=628; CY=1262
# fin Kaggle : chat qui panique (images 24-74), puis porche vide (image 115) tenu 1,3 s
true || ffmpeg -v error -y -i fuite1.mp4 -vf "trim=start_frame=24:end_frame=75,setpts=PTS-STARTPTS,minterpolate=fps=32:mi_mode=mci:mc_mode=aobmc:vsbmc=1,crop=1080:1920,unsharp=5:5:0.4" -c:v libx264 -crf 14 -preset fast up_fuite.mp4
ffmpeg -v error -y -sseof -0.05 -i up_chat_b.mp4 -frames:v 1 vide.png
ffmpeg -v error -y -i up_chat_a.mp4 -i up_chat_b.mp4 -loop 1 -i halo.png -i up_fuite4.mp4 -loop 1 -t 1.5 -framerate 32 -i vide.png -filter_complex "
[0:v]setpts=PTS-STARTPTS,fps=32,drawtext=$T:y=300:textfile=t1.txt:enable='lt(t,4.6)'[a];
[1:v]split=2[b0][bz];
[b0]trim=0:$TC,setpts=PTS-STARTPTS[b1];
[bz]trim=start=$TC,setpts=PTS-STARTPTS,select=eq(n\,0),loop=32:1:0,setpts=N/32/TB[zs];
[2:v]scale=380:380,format=rgba[h];
[zs][h]overlay=x=$CX-190:y=$CY-250:enable='gte(n,4)*not(between(n,11,12))':shortest=1,
 zoompan=z='if(lt(on,8),1+on*0.2,2.6)':x='max(0,min(iw-iw/zoom,$CX-iw/zoom/2+if(gte(on,8),10*sin(on*1.7),0)))':y='max(0,min(ih-ih/zoom,$CY-ih/zoom/2+if(gte(on,8),10*cos(on*2.3),0)))':d=1:s=1080x1920:fps=32,
 drawbox=c=white@0.8:t=fill:enable='between(n,8,9)',trim=end_frame=32,setpts=PTS-STARTPTS[z];
[3:v]setpts=PTS-STARTPTS,fps=32,setsar=1[f];
[4:v]fps=32,format=yuv420p,setsar=1[e];
[f]format=yuv420p[f2];[f2][e]xfade=transition=zoomin:duration=0.2:offset=2.019,drawtext=$T:y=300:textfile=t2.txt:enable='gte(t,2.169)'[fe];
[a][b1][z][fe]concat=n=4:v=1:a=0,format=yuv420p[v]" -map "[v]" -c:v libx264 -crf 17 -preset medium -r 32 muet.mp4
DUR=$(ffprobe -v error -show_entries format=duration -of csv=p=0 muet.mp4); echo dur $DUR
FD=$(ffprobe -v error -show_entries format=duration -of csv=p=0 up_fuite.mp4); echo fuite $FD
# Son : une piste par son, calée par adelay puis apad=whole_dur (atrim après apad décalait tout d'environ 1 s)
A=/mnt/project-files/sons; DUR=11.6875
ffmpeg -v error -y -i $A/toccata0.ogg -af "atrim=start=0.8,asetpts=PTS-STARTPTS,atrim=0:6.5,afade=t=out:st=6.35:d=0.15,adelay=1000|1000,volume=0.8,apad=whole_dur=$DUR,aresample=48000" -ac 2 m.wav
ffmpeg -v error -y -i $A/tonnerre0.ogg -af "atrim=start=10.75,asetpts=PTS-STARTPTS,atrim=0:2.3,afade=t=out:st=1.6:d=0.6,adelay=7500|7500,apad=whole_dur=$DUR,aresample=48000" -ac 2 tn.wav
ffmpeg -v error -y -i $A/feulement3.wav -af "atrim=start=0.95,asetpts=PTS-STARTPTS,atrim=0:0.5,afade=t=out:st=0.35:d=0.15,adelay=9750|9750,volume=2.2,apad=whole_dur=$DUR,aresample=48000" -ac 2 s.wav
ffmpeg -v error -y -i m.wav -i tn.wav -i s.wav -filter_complex "[0][1][2]amix=inputs=3:normalize=0,loudnorm=I=-14:TP=-1.5,aresample=48000[a]" -map "[a]" mix.wav
ffmpeg -v error -y -i muet.mp4 -i mix.wav -map 0:v -map 1:a -c:v copy -c:a aac -b:a 192k son.mp4
