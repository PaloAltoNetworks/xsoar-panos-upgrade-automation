mkdir ../Packs/AllCustomContent
demisto-sdk download --insecure -a -o ../Packs/AllCustomContent/
cd ../Packs/AllCustomContent
for line in `egrep -r "Network Operations" */* | awk -F: '{print $1}' | sort | uniq | grep -v Integrations | grep -v Scripts` ; do cp $line ../PAN_OS_Upgrade_Services/$line ; done
