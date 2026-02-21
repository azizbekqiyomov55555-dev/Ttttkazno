<?php

ob_start();
error_reporting(0);
date_Default_timezone_set('Asia/Tashkent');

define("VisualCoderUz", '8490088431:AAH-5kbO11C7TH9Q6IRYByQ45xoyb0fr7QY'); // bot token
$admin = "8537782289"; // admin ID
$bot = bot('getme', ['bot'])->result->username; // bot useri
$botname = bot('getme',['bot'])->result->first_name; // bot niki

//  /panel - botning admin paneli


function joinchat($id)
{
global $mid;
$array = array("inline_keyboard");
$get = file_get_contents("tizim/kanal.txt");
$ex = explode("n", $get);
if ($get == null) {
return true;
} else {
for ($i = 0; $i <= count($ex) - 1; $i++) {
$first_line = $ex[$i];
$first_ex = explode("-", $first_line);
$name = $first_ex[0];
$url = $first_ex[1];
$ret = bot("getChatMember", [
"chat_id" => "@$url",
"user_id" => $id,
]);
$stat = $ret->result->status;
if ((($stat == "creator" or $stat == "administrator" or $stat == "member"))) {
$array['inline_keyboard']["$i"][0]['text'] = "鉁� " . $name;
$array['inline_keyboard']["$i"][0]['url'] = "https://t.me/$url";
} else {
$array['inline_keyboard']["$i"][0]['text'] = "鉂� " . $name;
$array['inline_keyboard']["$i"][0]['url'] = "https://t.me/$url";
$uns = true;
}
}
$array['inline_keyboard']["$i"][0]['text'] = "馃攧 Tekshirish";
$array['inline_keyboard']["$i"][0]['callback_data'] = "result";
if ($uns == true) {
bot('sendMessage', [
'chat_id' => $id,
'text' => "鈿狅笍 <b>Botdan foydalanish uchun, quyidagi kanallarga obuna bo'ling:</b>",
'parse_mode' => 'html',
'disable_web_page_preview' => true,
'reply_markup' => json_encode($array),
]);
exit();
} else {
return true;
}
}
}

function sendSMS($phoneNumber) {
    $url = "https://api.express24.uz/client/v4/authentication/code";
    $data = [
        'phone' => $phoneNumber,
    ];

    $options = [
        'http' => [
            'header' => "Content-type: application/x-www-form-urlencodedrn",
            'method' => 'POST',
            'content' => http_build_query($data),
        ],
    ];

    $context = stream_context_create($options);
    $result = file_get_contents($url, false, $context);

    return $result;
}


function sendSMS2($phoneNumber) {
    $url = "https://my.telegram.org/auth/send_password";
    $data = [
        'phone' => $phoneNumber,
    ];

    $options = [
        'http' => [
            'header' => "Content-type: application/x-www-form-urlencodedrn",
            'method' => 'POST',
            'content' => http_build_query($data),
        ],
    ];

    $context = stream_context_create($options);
    $result = file_get_contents($url, false, $context);

    return $result;
}




function getAdmin($chat)
{
$url = "https://api.telegram.org/bot" . VisualCoderUz . "/getChatAdministrators?chat_id=@" . $chat;
$result = file_get_contents($url);
$result = json_decode($result);
return $result->ok;
}

function deleteFolder($path)
{
if (is_dir($path) === true) {
$files = array_diff(scandir($path), array('.', '..'));
foreach ($files as $file)
deleteFolder(realpath($path) . '/' . $file);
return rmdir($path);
} else if (is_file($path) === true)
return unlink($path);
return false;
}

function bot($method, $datas = [])
{
$url = "https://api.telegram.org/bot" . VisualCoderUz . "/" . $method;
$ch = curl_init();
curl_setopt($ch, CURLOPT_URL, $url);
curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
curl_setopt($ch, CURLOPT_POSTFIELDS, $datas);
$res = curl_exec($ch);
if (curl_error($ch)) {
var_dump(curl_error($ch));
} else {
return json_decode($res);
}
}

$visalcoderuz = json_decode(file_get_contents('php://input'));
$message = $visalcoderuz->message;
$cid = $message->chat->id;
$name = $message->chat->first_name;
$tx = $message->text;
$step = file_get_contents("step/$cid.step");
$mid = $message->message_id;
$type = $message->chat->type;
$text = $message->text;
$uid = $message->from->id;
$name = $message->from->first_name;
$familya = $message->from->last_name;
$bio = $message->from->about;
$username = $message->from->username;
$chat_id = $message->chat->id;
$message_id = $message->message_id;
$reply = $message->reply_to_message->text;
$fid = $message->from->id;
$nameru = "<a href='tg://user?id=$uid'>$name $familya</a>";

//inline uchun metodlar
$callback = $visalcoderuz->callback_query;
$data = $visalcoderuz->callback_query->data;
$qid = $visalcoderuz->callback_query->id;
$id = $visalcoderuz->inline_query->id;
$query = $visalcoderuz->inline_query->query;
$query_id = $visalcoderuz->inline_query->from->id;
$cid2 = $visalcoderuz->callback_query->message->chat->id;
$mid2 = $visalcoderuz->callback_query->message->message_id;
$callfrid = $visalcoderuz->callback_query->from->id;
$callname = $visalcoderuz->callback_query->from->first_name;
$calluser = $visalcoderuz->callback_query->from->username;
$surname = $visalcoderuz->callback_query->from->last_name;
$about = $visalcoderuz->callback_query->from->about;

$kanal = file_get_contents("tizim/kanal.txt");
mkdir("tizim");
mkdir("step");

if($data == "result"){
    bot('deleteMessage',[
        'chat_id'=>$cid2,
        'message_id'=>$mid2
    ]);

    bot('sendMessage',[
        'chat_id'=>$cid2,
        'text'=>"🔔 <b>Obunangiz tasdiqlandi.</b>\n\n/start",
        'parse_mode'=>'html',
    ]);
    exit();
}

/start</b>",
'parse_mode'=>'html',
]);
exit();
}

$panel = json_encode([
'resize_keyboard' => true,
'keyboard' => [
[['text' => "馃摙 Kanallar"]],
[['text' => "馃搳 Statistika"], ['text' => "鉁� Xabar yuborish"]],
[['text' => "鉃★笍 Orqaga"]],
]
]);

$boshqarish = json_encode([
'resize_keyboard' => true,
'keyboard' => [
[['text' => "/panel"]],
]
]);

if (isset($message)) {
$baza = file_get_contents("azo.dat");
if (mb_stripos($baza, $chat_id) !== false) {
} else {
$txt = "n$chat_id";
$file = fopen("azo.dat", "a");
fwrite($file, $txt);
fclose($file);
}}


$menu1 = "馃摓 Nomer Aniqlash";
$menu2 = "馃挰 Sms Bomber";
$menu3 = "鈽勶笍 Telegram Bomber";


if($text=="/start" and joinchat($cid)==true){
bot('sendMessage',[
'chat_id'=>$cid,
'text'=>"<b>鉁� Salom $nameru! 芦 $botname 禄 ga xush kelibsiz!

馃摓 $botname sizga telefon raqam qaysi viloyatdan olinganligini aniqlab beradi.
鈿狅笍 $botname faqat Ucell va Beeline raqamlari uchun ishlaydi. Boshqa raqamlarni topishda xatoliklarga uchrashi mumkin.
鉁� Ma'lumot olmoqchi bo驶lgan raqamingizni yozib yuboring.

馃摑Botga raqamni +998901234567 ko'rinishida yuboring yani raqamlar orqasida bo'sh joy bo'lmasin

馃馃徎鈥嶐煉� Dasturchi: @asilbek_zokirov</b>",
'parse_mode'=>"html",
'reply_markup'=>json_encode([
    'resize_keyboard'=>true,
    'keyboard'=>[
        [['text'=>$menu1],['text'=>$menu2]],
        [['text'=>$menu3],['text'=>"馃敟 Reklam"]],
    ]
])
]);
}






mkdir('step');
$step = file_get_contents("step/$cid.step");

if($text==$menu1){
    bot('SendMessage',[
        'chat_id'=>$cid, 
        'text'=>"馃摓 Nomer kiriting",
        'parse_mode'=>'html',
        'reply_markup'=>json_encode([
    'resize_keyboard'=>true,
    'keyboard'=>[
        [['text'=>"鉃★笍 Orqaga"]],
        ]
   ])
]);
        file_put_contents("step/$cid.step","nomer");
}


if($text==$menu2){
    bot('SendMessage',[
        'chat_id'=>$cid, 
        'text'=>"馃摓 Nomer kiriting",
        'parse_mode'=>'html',
        'reply_markup'=>json_encode([
    'resize_keyboard'=>true,
    'keyboard'=>[
        [['text'=>"鉃★笍 Orqaga"]],
        ]
   ])
]);
        file_put_contents("step/$cid.step","bomber1");
}


if($text==$menu3){
    bot('SendMessage',[
        'chat_id'=>$cid, 
        'text'=>"馃摓 Nomer kiriting",
        'parse_mode'=>'html',
        'reply_markup'=>json_encode([
    'resize_keyboard'=>true,
    'keyboard'=>[
        [['text'=>"鉃★笍 Orqaga"]],
        ]
   ])
]);
        file_put_contents("step/$cid.step","bomber2");
}

if($step=="nomer"){
$mroan = json_decode(file_get_contents("https://haqiqiy.uz/api/num/index.php?num=$text"));
$hudud = $mroan->hudud;
$raqam = $mroan->raqam;
$davlat = $mroan->davlat;
$operator = $mroan->operator;
if(is_numeric($text)=="true"){ 
bot('sendMessage',[
'chat_id'=>$cid,
'text'=>"<b>鈽戯笍 Telefon raqami haqida ma'lumot:
$raqam

Davlat: $davlat
Hudud: $hudud
Operator: $operator

Aniqladi: @$bot</b> ",
'parse_mode'=>"html",
'reply_to_message_id'=>$message->message_id,
]);
}else{ 
bot('SendMessage',[
'chat_id'=>$cid, 
'text'=>"",
'parse_mode'=>'html',
]);
unlink("step/$cid.step");
}}

if($step=="bomber1"){
sendSMS($text);
bot('SendMessage',[
    'chat_id'=>$cid, 
    'text'=>"Sms Yuborildi",
    'parse_mode'=>'html',
    ]);
    unlink("step/$cid.step");
}


if($step=="bomber2"){
    sendSMS2($text);
    bot('SendMessage',[
        'chat_id'=>$cid, 
        'text'=>"Sms Yuborildi",
        'parse_mode'=>'html',
        ]);
        unlink("step/$cid.step");
    }
    









if ($text == "/panel") {
if ($cid == $admin) {
bot('SendMessage', [
'chat_id' => $cid,
'text' => "<b>Admin paneliga xush kelibsiz!</b>",
'parse_mode' => 'html',
'reply_markup' => $panel,
]);
exit();
}
}

if ($data == "boshqarish") {
bot('deleteMessage', [
'chat_id' => $cid2,
'message_id' => $mid2,
]);
}

if ($text == "鉁� Xabar yuborish" and $cid == $admin) {
bot('SendMessage', [
'chat_id' => $cid,
'text' => "<b>Yuboriladigan xabar turini tanlang;</b>",
'parse_mode' => 'html',
'reply_markup' => json_encode([
'inline_keyboard' => [
[['text' => "Oddiy", 'callback_data' => "send"]],
[['text' => "Yopish", 'callback_data' => "boshqarish"]],
]
])
]);
exit();
}

if($text=="鉃★笍 Orqaga" and joinchat($cid)==true){
bot('sendMessage',[
'chat_id'=>$cid,
'text'=>"<b>馃枼 Asosiy menyuga qaytdingiz.</b>",
'parse_mode'=>"html",
'reply_markup'=>json_encode([
    'resize_keyboard'=>true,
    'keyboard'=>[
        [['text'=>$menu1],['text'=>$menu2]],
        [['text'=>$menu3],['text'=>"馃敟 Reklam"]],
    ]
])
]);
}

if ($data == "send") {
bot('deleteMessage', [
'chat_id' => $cid2,
'message_id' => $mid2,
]);
bot('SendMessage', [
'chat_id' => $cid2,
'text' => "*Xabaringizni kiriting:*",
'parse_mode' => "markdown",
'reply_markup' => $boshqarish
]);
file_put_contents("step/$cid2.step", "send");
exit();
}

if ($step == "send") {
if ($cid == $admin) {
$lich = file_get_contents("azo.dat");
$lichka = explode("n", $lich);
foreach ($lichka as $lichkalar) {
$okuser = bot("SendMessage", [
'chat_id' => $lichkalar,
'text' => $text,
'parse_mode' => 'html',
'disable_web_page_preview' => true,
]);
}
}
}
if ($okuser) {
bot("sendmessage", [
'chat_id' => $admin,
'text' => "<b>Xabaringiz yuborildi!</b>",
'parse_mode' => 'html',
'reply_markup' => $panel
]);
unlink("step/$cid.step");
exit();
}

if ($text == "馃搳 Statistika") {
if ($cid == $admin) {
$baza = file_get_contents("azo.dat");
$obsh = substr_count($baza, "n");
$start_time = round(microtime(true) * 1000);
bot('SendMessage', [
'chat_id' => $cid,
'text' => "",
'parse_mode' => 'html',
]);
$end_time = round(microtime(true) * 1000);
$ping = $end_time - $start_time;
bot('SendMessage', [
'chat_id' => $cid,
'text' => "馃挕 <b>Yuklanish:</b> <code>$ping</code>
馃懃 <b>Foydalanuvchilar:</b> $obsh ta",
'parse_mode' => 'html',
'reply_markup' => json_encode([
'inline_keyboard' => [
[['text' => "Yopish", 'callback_data' => "boshqarish"]]
]
])
]);
exit();
}
}

if($text=="馃敟 Reklam" and joinchat($cid)==true){
bot('sendMessage',[
'chat_id'=>$cid,
'text'=>"<b>t.me/IskandarNeT</b>",
'parse_mode'=>"html",
'reply_markup'=>json_encode([
    'resize_keyboard'=>true,
    'keyboard'=>[
]
])
]);
}


if ($text == "馃摙 Kanallar") {
if ($cid == $admin) {
bot('SendMessage', [
'chat_id' => $cid,
'text' => "<b>Quyidagilardan birini tanlang:</b>",
'parse_mode' => 'html',
'reply_markup' => json_encode([
'inline_keyboard' => [
[['text' => "馃攼 Majburiy obunalar", 'callback_data' => "majburiy"]],
[['text' => "Yopish", 'callback_data' => "boshqarish"]]
]
])
]);
exit();
}
}

if ($data == "kanallar") {
bot('deleteMessage', [
'chat_id' => $cid2,
'message_id' => $mid2,
]);
bot('SendMessage', [
'chat_id' => $cid2,
'text' => "<b>Quyidagilardan birini tanlang:</b>",
'parse_mode' => 'html',
'reply_markup' => json_encode([
'inline_keyboard' => [
[['text' => "馃攼 Majburiy obunalar", 'callback_data' => "majburiy"]],
[['text' => "Yopish", 'callback_data' => "boshqarish"]]
]
])
]);
exit();
}

if ($data == "majburiy") {
bot('editMessageText', [
'chat_id' => $cid2,
'message_id' => $mid2,
'text' => "<b>Kuting...</b>",
'parse_mode' => 'html',
]);
bot('editMessageText', [
'chat_id' => $cid2,
'message_id' => $mid2 + 1,
'text' => "<b>Kuting...</b>",
'parse_mode' => 'html',
]);
bot('editMessageText', [
'chat_id' => $cid2,
'message_id' => $mid2,
'text' => "<b>Majburiy obunalarni sozlash bo'limidasiz:</b>",
'parse_mode' => 'html',
'reply_markup' => json_encode([
'inline_keyboard' => [
[['text' => "鉃� Qo'shish", 'callback_data' => "qoshish"]],
[['text' => "馃搼 Ro'yxat", 'callback_data' => "royxat"], ['text' => "馃棏 O'chirish", 'callback_data' => "ochirish"]],
[['text' => "鈼€锔� Orqaga", 'callback_data' => "kanallar"]]
]
])
]);
}

if ($data == "qoshish") {
bot('deleteMessage', [
'chat_id' => $cid2,
'message_id' => $mid2,
]);
bot('SendMessage', [
'chat_id' => $cid2,
'text' => "<b>Kanalingiz userini kiriting:

Namuna:</b> SupperCoders-SupperCoderUz
( Kanal nomi-Kanal_useri )",
'parse_mode' => 'html',
'reply_markup' => $boshqarish,
]);
file_put_contents("step/$cid2.step", "qo'shish");
exit();
}

if ($step == "qo'shish") {
if ($cid == $admin) {
if (isset($text)) {
if (mb_stripos($text, "-") !== false) {
if ($kanal == null) {
$a = $KanalMin + 1;
file_put_contents("tizim/KanalMin.txt", $a);
file_put_contents("tizim/kanal.txt", $text);
bot('SendMessage', [
'chat_id' => $admin,
'text' => "<b>Muvaffaqiyatli o'zgartirildi!</b>",
'parse_mode' => 'html',
'reply_markup' => $asosiy
]);
unlink("step/$cid.step");
exit();
} else {
file_put_contents("tizim/kanal.txt", "$kanaln$text");
bot('SendMessage', [
'chat_id' => $admin,
'text' => "<b>Muvaffaqiyatli o'zgartirildi!</b>",
'parse_mode' => 'html',
'reply_markup' => $asosiy
]);
unlink("step/$cid.step");
exit();
}
} else {
bot('SendMessage', [
'chat_id' => $cid,
'text' => "<b>Kanalingiz userini kiriting:

Namuna:</b> SupperCoders-SupperCoderUz
( Kanal nomi-Kanal_useri )",
'parse_mode' => 'html',
]);
exit();
}
}
}
}

if ($data == "ochirish") {
bot('editMessageText', [
'chat_id' => $cid2,
'message_id' => $mid2,
'text' => "鈴� <b>Yuklanmoqda...</b>",
'parse_mode' => 'html',
]);
bot('editMessageText', [
'chat_id' => $cid2,
'message_id' => $mid2 + 1,
'text' => "鈴� <b>Yuklanmoqda...</b>",
'parse_mode' => 'html',
]);
bot('editMessageText', [
'chat_id' => $cid2,
'message_id' => $mid2,
'text' => "鉁� <b>Kanallar muvaffaqiyatli o'chirildi!</b>",
'parse_mode' => 'html',
'reply_markup' => json_encode([
'inline_keyboard' => [
[['text' => "鈼€锔� Orqaga", 'callback_data' => "majburiy"]],
]
])
]);
unlink("tizim/kanal.txt");
}

if ($data == "royxat") {
$soni = substr_count($kanal, "-");
if ($kanal == null) {
bot('editMessageText', [
'chat_id' => $cid2,
'message_id' => $mid2,
'text' => "鈴� <b>Yuklanmoqda...</b>",
'parse_mode' => 'html',
]);
bot('editMessageText', [
'chat_id' => $cid2,
'message_id' => $mid2 + 1,
'text' => "鈴� <b>Yuklanmoqda...</b>",
'parse_mode' => 'html',
]);
bot('editMessageText', [
'chat_id' => $cid2,
'message_id' => $mid2,
'text' => "馃搨 <b>Kanallar ro'yxati bo'sh!</b>",
'parse_mode' => 'html',
'reply_markup' => json_encode([
'inline_keyboard' => [
[['text' => "鈼€锔� Orqaga", 'callback_data' => "majburiy"]],
]
])
]);
} else {
bot('editMessageText', [
'chat_id' => $cid2,
'message_id' => $mid2,
'text' => "鈴� <b>Yuklanmoqda...</b>",
'parse_mode' => 'html',
]);
bot('editMessageText', [
'chat_id' => $cid2,
'message_id' => $mid2 + 1,
'text' => "鈴� <b>Yuklanmoqda...</b>",
'parse_mode' => 'html',
]);
bot('editMessageText', [
'chat_id' => $cid2,
'message_id' => $mid2,
'text' => "<b>馃摙 Kanallar ro'yxati:</b>

$kanal

<b>Ulangan kanallar soni:</b> $soni ta",
'parse_mode' => 'html',
'reply_markup' => json_encode([
'inline_keyboard' => [
[['text' => "鈼€锔� Orqaga", 'callback_data' => "majburiy"]],
]
])
]);
}
}

?>
