# Export_Web_Kiosk_Content.ps1


# Output only Web Enabled EmbARK content that has changed in the last few days
$queryDate = [DateTime]::Now.AddDays(-2).ToString("MM/dd/yyyy")
# $urlMod = -join("http://localhost:8080/results.html?layout=marble_vracore4_plus_dcterms&format=xml&maximumrecords=-1&recordType=objects_1&query=mod_date%3E%22", $queryDate, "%22")
$urlMod = -join("http://localhost:8080/results.html?layout=marble_mets&format=xml&maximumrecords=-1&recordType=objects_1&query=mod_date%3E%22", $queryDate, "%22")
# Write-Host $urlMod
Invoke-RestMethod -Uri $urlMod -TimeoutSec 1800 -OutFile Modified_Web_Kiosk_Mets_Output.xml

# Output all Web Enabled EmbARK content
# $urlAll = "http://localhost:8080/results.html?layout=marble_vracore4_plus_dcterms&format=xml&maximumrecords=-1&recordType=objects_1&query=_ID=ALL"
$urlAll = "http://localhost:8080/results.html?layout=marble_mets&format=xml&maximumrecords=-1&recordType=objects_1&query=_ID=ALL"
Invoke-RestMethod -Uri $urlAll -TimeoutSec 1800 -OutFile Full_Web_Kiosk_Mets_Output.xml

