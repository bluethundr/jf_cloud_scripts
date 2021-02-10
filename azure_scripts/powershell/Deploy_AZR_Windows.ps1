Login-AzureRmAccount
select-AzureRmSubscription -SubscriptionName "Lighthouse.Dev"
select-AzureRmSubscription -SubscriptionName "Asset.Core.Prod"
$folder = "C:\Users\tdunphy\Desktop\important_folders\Projects\KLT\repo\MS-Azure-Cloud\Templates\VirtualMachines\KTECHWindowsImage\" #Must end in trailing slash.
$rg = "rg-lghtdev-core1"
$template = "azuredeploy.NOavset.json"
$param = "WindowsDeploymentParameters\USAZRKPAP00019.json"
Test-AzureRmResourceGroupDeployment -ResourceGroupName $rg -TemplateFile ($folder + $template) -TemplateParameterFile ($folder + $param) -Verbose
New-AzureRmResourceGroupDeployment -ResourceGroupName $rg -TemplateFile ($folder + $template) -TemplateParameterFile ($folder + $param) -Verbose 