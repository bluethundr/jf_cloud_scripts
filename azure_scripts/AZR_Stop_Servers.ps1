## Shut Down Azure Servers
Login-AzureRmAccount
Set-AzureRmContext -Subscription Asset.Core.Prod
echo "Stopping USAZRKPCL10072"
Stop-AzureRmVM -ResourceGroupName "rg-prodspectrum-klt-shared" -Name "USAZRKPCL10072"
sleep 5
echo "Stopping USAZRCPAP00002"
Stop-AzureRmVM -ResourceGroupName "rg-prodspectrum-core1" -Name "USAZRCPAP00002"
sleep 5
echo "Stopping USAZRKDAP00019"
Stop-AzureRmVM -ResourceGroupName "rg-prodspectrum-core1" -Name "USAZRCPAP00004"
sleep 5


