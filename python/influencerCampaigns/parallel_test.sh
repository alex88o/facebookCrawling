# cat IDs.txt | parallel python dailyAnalysis.py '{= s/\r// =}' 20 '>' '{= s/\r// =}'.output '2>' '{= s/\r// =}'.error
#cat IDs.txt | parallel python influencerCampaigns.py '{= s/\r// =}' 20 25 231
#cat influencers.txt | parallel python influencerCampaigns.py '{= s/\r// =}' '>' '{= s/\r// =}'.out '2>' '{= s/\r// =}'.err
cat influencers.txt | parallel python influencerCampaigns.py '{= s/\r// =}'
