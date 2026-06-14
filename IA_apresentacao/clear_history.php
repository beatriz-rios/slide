<?php
header('Content-Type: application/json');

// Limpar history.json
$historyFile = __DIR__ . DIRECTORY_SEPARATOR . 'history.json';
file_put_contents($historyFile, '[]');

// Limpar imagens da pasta captures
$capturesDir = dirname(__DIR__) . DIRECTORY_SEPARATOR . 'captures';
if (is_dir($capturesDir)) {
    $files = glob($capturesDir . DIRECTORY_SEPARATOR . '*.jpg');
    foreach ($files as $file) {
        @unlink($file);
    }
}

echo json_encode(["status" => "success"]);
?>
