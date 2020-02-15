Login-AzureRmAccount
set DOCS "C:\Users\tdunphy\Desktop\important_folders\azure\docs\public_ips"
$a = Get-Date -format M-d-yyyy
Get-AzureRmSubscription | %{Select-AzureRmSubscription -SubscriptionName $_.SubscriptionName;Get-AzureRmPublicIpAddress | Select Name,ResourceGroupName,Location,IpAddress | convertto-csv -NoTypeInformation}  > $DOCS\AZR_Public_IPs-$a.csv