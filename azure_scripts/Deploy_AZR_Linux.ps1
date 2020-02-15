Login-AzureRmAccount
#select-AzureRmSubscription -SubscriptionName "Lighthouse.Dev"
select-AzureRmSubscription -SubscriptionName "Asset.Core.Prod"

$folder = "C:\Users\tdunphy\Desktop\important_folders\Projects\KLT\repo\MS-Azure-Cloud\Templates\VirtualMachines\KTECHLinuxImageAvSet\" #Must end in trailing slash.
$rg = "rg-prodspectrum-klt-shared"
$template = "azuredeploy_unmanaged.json"
$param = "LinuxDeploymentsParameters\USAZRKLXP00042.json"
Test-AzureRmResourceGroupDeployment -ResourceGroupName $rg -TemplateFile ($folder + $template) -TemplateParameterFile ($folder + $param) -Verbose
New-AzureRmResourceGroupDeployment -ResourceGroupName $rg -TemplateFile ($folder + $template) -TemplateParameterFile ($folder + $param) -Verbose 