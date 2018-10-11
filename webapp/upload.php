<?php
if ($_SERVER['REQUEST_METHOD'] == 'POST') {

   $target_dir = "/var/www/html/uploads/";
   $target_file = $target_dir . strval(rand(100000000000, 999999999999));
   $sourcename = '';
   if ($_GET['method'] == 'upload') {
      $sourcename = $_FILES['userfile']['name'];
   } elseif ($_GET['method'] == 'copyurl') {
     $sourcename = $_GET['url'];
   } elseif ($_GET['method'] == 'example') {
     $sourcename = "/var/www/html/examples/" . $_GET['filename'];
   }
   $inputsuffix = strtolower(substr($sourcename,-4));
   if ($inputsuffix == '.mp3') {
      $target_file = $target_file . '.mp3';
   } elseif ($inputsuffix == '.wav') {
      $target_file = $target_file . '.wav';
   }

   $sourcearg = '';
   if ($_GET['method'] == 'upload') {
      move_uploaded_file($_FILES['userfile']['tmp_name'], $target_file);
   } elseif ($_GET['method'] == 'copyurl') {
     //copy($_GET['url'], $target_file);
     $sourcearg = ' "' . $sourcename . '"';
   } elseif ($_GET['method'] == 'example') {
     copy($sourcename, $target_file);
   } else {
     echo "! Error: Invalid method argument";
   }
   
   $command = '/var/www/html/predict.py ' . $target_file . $sourcearg;
   //$command = '/var/www/html/predict.py ' . $target_file . $sourcearg . ' 2>&1';
   $output = shell_exec($command);
   echo $output;

}
?>
