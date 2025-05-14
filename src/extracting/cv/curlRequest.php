<?php

if ($argc < 3){
    die("Usage: php php_script.php <input_file> <output_file>\n");
}

$inputFile = $argv[1];
$outputFile = $argv[2];

$fileContent = file_get_contents($inputFile);


if ($fileContent === false) {
    die("Failed to read file: $filePath");
}

$params = array(
        'action'                => 'process_cv',
        'customerKey'           => 'TRESCON',
        'instanceName'          => 'TRESCON',
        'instanceDbVersion'     => '21.06.21',
        'language'              => 'DE',
        'attachmentId'          => '1',
        'attachmentSequNr'      => '1',
        'attachmentFilePath'    => $inputFile,
        'fileContent'           => base64_encode( $fileContent ),
        'ServerPort_ConvertCV'  => "",
        'ServerPort_ProcessCV'  => "http://ccdemo.daxtra.com",
);

function curl_request($url, $method, &$errorNo, &$errorStr, $params = null)
{
    if ($method == 'GET' && is_array($params))
    {
        if (strpos($url, '?') === false)
        {
            if ($url[strlen($url)-1] != '/')
                $url .= '/';

            $url .= "?";
        }
        foreach ($params as $key => $value)
        {
            $url .= urlencode($key).'='.urlencode($value).'&';
        }
        $url = chop($url); // drop last &
    }

    $ch = curl_init();

    curl_setopt($ch, CURLOPT_URL, $url);
    curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
    curl_setopt($ch, CURLOPT_SSL_VERIFYPEER, false);
    curl_setopt($ch, CURLOPT_SSL_VERIFYHOST, false);
    curl_setopt($ch, CURLOPT_NOSIGNAL, true);

    # brauchen wir nicht, ist eine andere Funktionalität von Fecher, geht auch ohne
    #$serverConfig = FTools::read_keyvaluepair_file('/fecher/config/configuration');

    if ($method == 'POST')
    {
        curl_setopt($ch, CURLOPT_POST, 1);
        curl_setopt($ch, CURLOPT_POSTFIELDS, $params);
    }

    $curlResult = curl_exec($ch);

    $errorNo  = curl_errno($ch);

    if ($errorNo)
    {
        $errorStr = curl_error($ch);
        return false;
    }

    curl_close($ch);

    return $curlResult;
}

$errorNo = $errorStr = null;
$processCvResult_json = curl_request('https://daxtra-api.hunter-software.eu/v2/', 'POST', $errorNo, $errorStr, $params);


if ($processCvResult_json === false) {
    echo "CURL Error ($errorNo): $errorStr\n";
    die("CURL Error ($errNo): $errorStr");
}

$processCvResult = json_decode($processCvResult_json, true);

if (file_put_contents($outputFile, $processCvResult_json)) {
    echo "The result has been successfully saved to: $outputFile\n";
} else {
    die("Failed to save the result to: $outputFile\n");
}

?>
