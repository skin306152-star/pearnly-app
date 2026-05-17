<?php
/**
 * Pearnly Bridge API  v1.0
 * 放到 MR.ERP 根目录（和 index.php 同级）
 * 不修改任何原有文件，不影响 MR.ERP 正常运行
 *
 * 安装后测试：
 * https://你的ERP域名/pearnly_bridge.php?key=你设定的密钥&action=ping
 */

// ============================================================
// 【客户填写区】只需要改这里
// ============================================================

// 1. 双方约定的 API 密钥（填任意一串字符，告诉 Pearnly 团队）
define('PEARNLY_API_KEY', 'CHANGE_ME_TO_ANY_SECRET');

// 2. 数据库连接（从你的 config.php 或 conn.php 里复制）
define('DB_HOST',     'localhost');
define('DB_USER',     '');          // 数据库账号
define('DB_PASS',     '');          // 数据库密码
define('DB_NAME',     '');          // 数据库名称
define('DB_PORT',     3306);
define('DB_CHARSET',  'utf8');

// 3. 允许请求的 IP（留空 = 允许所有；填 Pearnly 服务器 IP = 更安全）
define('ALLOWED_IP', '');  // 例：'45.76.53.194'

// ============================================================
// 以下不需要修改
// ============================================================

header('Content-Type: application/json; charset=utf-8');
header('X-Powered-By: Pearnly Bridge');

// IP 白名单
if (ALLOWED_IP !== '') {
    $client_ip = $_SERVER['HTTP_X_FORWARDED_FOR']
        ?? $_SERVER['REMOTE_ADDR']
        ?? '';
    if (trim(explode(',', $client_ip)[0]) !== ALLOWED_IP) {
        http_response_code(403);
        die(json_encode(['ok' => false, 'error' => 'ip_forbidden']));
    }
}

// API Key 鉴权
$req_key = $_GET['key'] ?? $_SERVER['HTTP_X_API_KEY'] ?? '';
if ($req_key !== PEARNLY_API_KEY || PEARNLY_API_KEY === 'CHANGE_ME_TO_ANY_SECRET') {
    http_response_code(403);
    die(json_encode(['ok' => false, 'error' => 'forbidden']));
}

// 数据库连接
$conn = new mysqli(DB_HOST, DB_USER, DB_PASS, DB_NAME, DB_PORT);
if ($conn->connect_errno) {
    http_response_code(500);
    die(json_encode(['ok' => false, 'error' => 'db_connect_failed']));
}
$conn->set_charset(DB_CHARSET);

// 路由
$action = strtolower(trim($_GET['action'] ?? ''));

// ---- ping / 健康检查 ----
if ($action === 'ping') {
    echo json_encode([
        'ok'      => true,
        'action'  => 'ping',
        'db'      => $conn->server_info,
        'time'    => date('Y-m-d H:i:s'),
        'version' => '1.0',
    ]);

// ---- 商品主表（stkmas）----
} elseif ($action === 'products') {
    $limit  = min((int)($_GET['limit']  ?? 2000), 5000);
    $offset = max((int)($_GET['offset'] ?? 0), 0);
    $search = trim($_GET['search'] ?? '');

    $where = "1=1";
    $params = [];
    $types  = '';

    if ($search !== '') {
        $where .= " AND (code LIKE ? OR name LIKE ?)";
        $like = '%' . $search . '%';
        $params[] = $like;
        $params[] = $like;
        $types   .= 'ss';
    }

    $sql = "SELECT code, name, unit, type1 AS type, status
            FROM stkmas
            WHERE $where
            ORDER BY code
            LIMIT ? OFFSET ?";
    $params[] = $limit;
    $params[] = $offset;
    $types   .= 'ii';

    $stmt = $conn->prepare($sql);
    if (!$stmt) {
        // 某些版本列名不同，尝试简化版
        $sql2 = "SELECT code, name, '' AS unit, '' AS type, status
                 FROM stkmas WHERE $where ORDER BY code LIMIT ? OFFSET ?";
        $stmt = $conn->prepare($sql2);
    }

    $stmt->bind_param($types, ...$params);
    $stmt->execute();
    $rows = $stmt->get_result()->fetch_all(MYSQLI_ASSOC);
    $stmt->close();

    echo json_encode([
        'ok'     => true,
        'items'  => $rows,
        'count'  => count($rows),
        'offset' => $offset,
    ]);

// ---- 客户主表（combrhcus）----
} elseif ($action === 'customers') {
    $limit  = min((int)($_GET['limit']  ?? 2000), 5000);
    $offset = max((int)($_GET['offset'] ?? 0), 0);
    $search = trim($_GET['search'] ?? '');

    $where = "1=1";
    $params = [];
    $types  = '';

    if ($search !== '') {
        $where .= " AND (code LIKE ? OR name LIKE ?)";
        $like = '%' . $search . '%';
        $params[] = $like;
        $params[] = $like;
        $types   .= 'ss';
    }

    $sql = "SELECT code, name, taxno AS tax_id, type1 AS type, status
            FROM combrhcus
            WHERE $where
            ORDER BY code
            LIMIT ? OFFSET ?";
    $params[] = $limit;
    $params[] = $offset;
    $types   .= 'ii';

    $stmt = $conn->prepare($sql);
    if (!$stmt) {
        $sql2 = "SELECT code, name, '' AS tax_id, '' AS type, status
                 FROM combrhcus WHERE $where ORDER BY code LIMIT ? OFFSET ?";
        $stmt = $conn->prepare($sql2);
    }

    $stmt->bind_param($types, ...$params);
    $stmt->execute();
    $rows = $stmt->get_result()->fetch_all(MYSQLI_ASSOC);
    $stmt->close();

    echo json_encode([
        'ok'     => true,
        'items'  => $rows,
        'count'  => count($rows),
        'offset' => $offset,
    ]);

// ---- 查询表结构（调试用，确认列名）----
} elseif ($action === 'schema') {
    $table = preg_replace('/[^a-zA-Z0-9_]/', '', $_GET['table'] ?? '');
    if (!in_array($table, ['stkmas', 'combrhcus', 'armas', 'armasd'])) {
        echo json_encode(['ok' => false, 'error' => 'table_not_allowed']);
        $conn->close();
        exit;
    }
    $result = $conn->query("DESCRIBE `$table`");
    $cols = $result ? $result->fetch_all(MYSQLI_ASSOC) : [];
    echo json_encode(['ok' => true, 'table' => $table, 'columns' => $cols]);

// ---- 未知 action ----
} else {
    http_response_code(400);
    echo json_encode([
        'ok'    => false,
        'error' => 'unknown_action',
        'hint'  => 'available: ping, products, customers, schema',
    ]);
}

$conn->close();
