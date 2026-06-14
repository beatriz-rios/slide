<?php
header('Content-Type: application/json');

// Verifica se a porta 5000 já está respondendo (servidor já está rodando)
$socket = @fsockopen('127.0.0.1', 5000, $errno, $errstr, 1);
if ($socket) {
    fclose($socket);
    echo json_encode(["status" => "already_running"]);
    exit;
}

// Servidor não está rodando - iniciar
$cmd = '"C:\Users\Triz\AppData\Local\Programs\Python\Python311\python.exe" IA_apresentacao\detector_web.py > detector_log.txt 2>&1';
pclose(popen('start /B "" ' . $cmd, "r"));
echo json_encode(["status" => "started"]);
?>
