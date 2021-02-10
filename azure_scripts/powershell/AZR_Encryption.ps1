## Log Into Azure
Login-AzureRmAccount
select-AzureRmSubscription -SubscriptionName "Asset.Core.Prod"

## Select the Subscription


######## Block 1: Encryption script block for Windows & Linux instances ##########################
##### Set-AzureRmVMDiskEncryptionExtension - run this command for Linux and Windows as following:
# Windows: -VolumeType All
# Linux:   -VolumeType OS (if necessary -VolumeType Data)
# Add -SkipVmBackup parameter for the managed disks
#################################################################################################

$vmNameForEncryption = 'usazrklxp00041'
$resourceGroupName = 'rg-prodspectrum-klt-shared'
$aadClientID = '797a34c2-8ab2-4bbd-8af9-11b23db1f58f'
$aadClientSecret ='f09e513b-192a-4767-a705-ec592cc92047'
$vaultName = 'kv-prodasset-crypt'
$keyVaultResourceId = '/subscriptions/0a0771b3-ac60-431c-bea1-070f53f54625/resourceGroups/rg-ktech-security/providers/Microsoft.KeyVault/vaults/kv-prodasset-crypt'
$diskEncryptionKeyVaultUrl = "https://$vaultName.vault.azure.net/"

Set-AzureRmVMDiskEncryptionExtension -ResourceGroupName $resourceGroupName -VMName $vmNameForEncryption -AadClientID $aadClientID -AadClientSecret $aadClientSecret -DiskEncryptionKeyVaultUrl $diskEncryptionKeyVaultUrl -DiskEncryptionKeyVaultId $keyVaultResourceId -VolumeType OS -SkipVmBackup

############## End of the encryption block script ###########################################
#############################################################################################


######### Block 2: Assign "MachineName" tag for Linux instance. Do not run Block 2 for Windows VMs #################
$redhatVM = Get-AzureRmVM -ResourceGroupName $resourceGroupName -Name $vmNameForEncryption

If ($redhatVM.StorageProfile.OsDisk.OsType -eq "Linux")
    {
    #Get the secret
    $secretName = ($redhatVM.StorageProfile.OsDisk.EncryptionSettings.DiskEncryptionKey.SecretUrl).Split("/")[-2]
    #Get existing tags
    $secret = Get-AzureKeyVaultSecret -VaultName $vaultName -Name $secretName
    $existingTags = $secret.Attributes.Tags
    #Set new tags
    $newTags = $existingTags
    $newTags += @{MachineName=$vmNameForEncryption}
    Set-AzureKeyVaultSecretAttribute -VaultName $vaultName -Name $secretName -Tag $newTags
    }
Else
    {
        Write-Verbose "VM is Windows, no new tags are required"
    }


##### Block 3: Run this periodically to check on ecnryption status - "InProgress"; "PendingReboot"; "Encrypted" 
##### If "InProgress" takes longer than 30 minutes, ecnryption probably has failed ######################
Get-AzureRmVMDiskEncryptionStatus -ResourceGroupName $resourceGroupName -VMName $vmNameForEncryption



 
<# Run this command to delete unwated tag, Delete tag option is not available in the console

$newTags = $existingTags
$newTags.Remove("VMNameX")

#> 
