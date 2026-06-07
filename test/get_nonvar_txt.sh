
datetimes=( 2026060716
            2026060717 
            2026060718 )

for d in ${datetimes[@]}; do
  mkdir ${d}
  cd ${d}
  curl -O https://rapidrefresh.noaa.gov/pyDAmonitor/rrfsv2x/${d}/nonvar_cloud_out.txt
  cd ..
done
