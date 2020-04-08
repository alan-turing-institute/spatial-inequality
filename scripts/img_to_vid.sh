
# For all sub-directories in the input directory:
    # Runs ffmpeg to create a video from all the .png files in that directory
for dir in "$1"/*
do
    echo $dir
    cd "$dir"
    ffmpeg -framerate 0.5 -pattern_type glob -i '*.png' -vcodec libx264 -pix_fmt yuv420p out.mp4
done

