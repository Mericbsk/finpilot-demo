<?php
header('Content-Type: application/json');

// Sadece POST isteklerini kabul et
if ($_SERVER["REQUEST_METHOD"] == "POST") {
    // Form verilerini al
    $email = filter_var(trim($_POST["email"]), FILTER_SANITIZE_EMAIL);

    // E-posta doğrulama
    if (!filter_var($email, FILTER_VALIDATE_EMAIL)) {
        http_response_code(400);
        echo json_encode(["ok" => false, "error" => "Geçersiz e-posta adresi."]);
        exit;
    }

    // Alıcı e-posta adresi (Kendi mail adresiniz)
    $recipient = "finpilot@finpilot.at";

    // E-posta konusu
    $subject = "Yeni Beta Bekleme Listesi Kaydı";

    // E-posta içeriği
    $email_content = "Yeni bir kullanıcı beta sürümü için kaydoldu:\n\n";
    $email_content .= "E-posta: $email\n";

    // E-posta başlıkları
    $headers = "From: noreply@finpilot.at\r\n";
    $headers .= "Reply-To: $email\r\n";
    $headers .= "X-Mailer: PHP/" . phpversion();

    // Maili gönder
    if (mail($recipient, $subject, $email_content, $headers)) {
        http_response_code(200);
        echo json_encode(["ok" => true, "message" => "Kaydınız başarıyla alındı!"]);
    } else {
        http_response_code(500);
        echo json_encode(["ok" => false, "error" => "Mesaj gönderilirken bir hata oluştu."]);
    }
} else {
    http_response_code(403);
    echo json_encode(["ok" => false, "error" => "Bu sayfaya doğrudan erişim yasaktır."]);
}
?>
