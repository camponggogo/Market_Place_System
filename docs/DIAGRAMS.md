# System Diagrams - Food Court Management System

## 1. System Overview Diagram

```mermaid
graph TB
    subgraph "Frontend Layer"
        WEB[Web Interface]
        MOBILE[Mobile App]
        LINE[LINE OA]
        POS[POS System]
    end
    
    subgraph "API Layer"
        API[FastAPI REST API]
        AUTH[Authentication]
        VALID[Validation]
    end
    
    subgraph "Business Logic"
        PH[Payment Hub]
        RS[Refund Service]
        CS[Crypto Service]
        TS[Tax Service]
        RPT[Report Service]
    end
    
    subgraph "Data Layer"
        DB[(MariaDB)]
        CACHE[(Cache)]
    end
    
    subgraph "External Services"
        BLOCK[Blockchain]
        LINE_API[LINE API]
        PROMPT[PromptPay]
        ETAX[E-Tax]
    end
    
    WEB --> API
    MOBILE --> API
    LINE --> API
    POS --> API
    
    API --> AUTH
    API --> VALID
    API --> PH
    API --> RS
    API --> CS
    API --> TS
    API --> RPT
    
    PH --> DB
    RS --> DB
    CS --> DB
    TS --> DB
    RPT --> DB
    
    PH --> CACHE
    RS --> CACHE
    
    CS --> BLOCK
    RS --> LINE_API
    PH --> PROMPT
    TS --> ETAX
```

## 2. Payment Processing Flow

```mermaid
flowchart TD
    START([ลูกค้าเริ่มต้น]) --> CHOOSE{เลือกวิธีชำระเงิน}
    
    CHOOSE -->|เงินสด| CASH[เงินสด]
    CHOOSE -->|Digital Wallet| WALLET[LINE Pay/Apple Pay/etc.]
    CHOOSE -->|Credit Card| CARD[Visa/Mastercard]
    CHOOSE -->|Crypto| CRYPTO[Bitcoin/ETH/etc.]
    
    CASH --> CREATE_ID[สร้าง Food Court ID]
    WALLET --> GATEWAY[Payment Gateway]
    CARD --> GATEWAY
    CRYPTO --> P2P[P2P Transaction]
    
    GATEWAY -->|Success| CREATE_ID
    P2P -->|Confirmed| CREATE_ID
    
    CREATE_ID --> STORE[ใช้ที่ร้านค้า]
    STORE --> CHECK{ยอดเงิน<br/>พอหรือไม่?}
    
    CHECK -->|พอ| DEDUCT[หักยอดเงิน]
    CHECK -->|ไม่พอ| ERROR[แสดงข้อผิดพลาด]
    
    DEDUCT --> REMAIN{ยอดเงิน<br/>เหลือหรือไม่?}
    
    REMAIN -->|เหลือ| REFUND[ขอคืนเงิน]
    REMAIN -->|ไม่เหลือ| COMPLETE([เสร็จสิ้น])
    
    REFUND --> COMPLETE
    ERROR --> START
```

## 3. Database Entity Relationship

```mermaid
erDiagram
    CUSTOMER {
        int id PK
        string phone UK
        string name
        string line_user_id
    }
    
    FOODCOURT_ID {
        string foodcourt_id PK
        int customer_id FK
        float initial_amount
        float current_balance
        enum payment_method
        string status
    }
    
    COUNTER_TRANSACTION {
        int id PK
        string foodcourt_id FK
        float amount
        enum payment_method
        datetime created_at
    }
    
    STORE_TRANSACTION {
        int id PK
        string foodcourt_id FK
        int store_id FK
        float amount
        datetime created_at
    }
    
    TRANSACTION {
        int id PK
        int customer_id FK
        int store_id FK
        string foodcourt_id FK
        float amount
        enum payment_method
        enum status
    }
    
    STORE {
        int id PK
        string name
        boolean crypto_enabled
    }
    
    TAX_INVOICE {
        int id PK
        int transaction_id FK
        string invoice_number UK
        float amount
        float vat_amount
        string payment_method
    }
    
    CUSTOMER ||--o{ FOODCOURT_ID : "owns"
    FOODCOURT_ID ||--o{ COUNTER_TRANSACTION : "created_by"
    FOODCOURT_ID ||--o{ STORE_TRANSACTION : "used_in"
    FOODCOURT_ID ||--o{ TRANSACTION : "linked_to"
    STORE ||--o{ STORE_TRANSACTION : "receives"
    STORE ||--o{ TRANSACTION : "has"
    TRANSACTION ||--o| TAX_INVOICE : "generates"
```

## 4. State Machine - Food Court ID

```mermaid
stateDiagram-v2
    [*] --> Created: Exchange Money
    Created --> Active: Success
    Active --> Used: All Balance Used
    Active --> PartiallyUsed: Some Balance Used
    PartiallyUsed --> Refunded: Request Refund
    PartiallyUsed --> Used: All Balance Used
    Used --> [*]
    Refunded --> [*]
    
    note right of Created
        Initial state
        Full balance available
    end note
    
    note right of Active
        Ready to use
        Full balance
    end note
    
    note right of PartiallyUsed
        Some transactions made
        Balance remaining
    end note
    
    note right of Used
        All balance used
        No refund needed
    end note
    
    note right of Refunded
        Remaining balance refunded
        Closed
    end note
```

## 5. E-Money Guard Flow

```mermaid
flowchart LR
    A[สิ้นวัน] --> B{มีใบอนุญาต<br/>e-Money?}
    
    B -->|ใช่| C[ปล่อยให้ยอดคงเหลือ]
    B -->|ไม่ใช่| D[ตรวจสอบยอดเงิน]
    
    D --> E{มียอดเงิน<br/>คงเหลือ?}
    
    E -->|ไม่| F[ไม่ต้องทำอะไร]
    E -->|ใช่| G[ส่งการแจ้งเตือน]
    
    G --> H{ลูกค้าเลือก<br/>วิธีคืนเงิน}
    
    H -->|เงินสด| I[คืนเงินที่เคาน์เตอร์]
    H -->|PromptPay| J[โอนคืนอัตโนมัติ]
    
    I --> K[เคลียร์ยอดเป็น 0]
    J --> K
    
    K --> L[สรุปยอดรายวัน]
    
    style B fill:#ffeb3b
    style G fill:#ff9800
    style K fill:#4caf50
```

## 6. Crypto P2P Flow

```mermaid
sequenceDiagram
    participant C as Customer
    participant S as Store
    participant SYS as System
    participant BC as Blockchain
    participant EXP as Explorer
    
    C->>S: เลือกชำระ Crypto
    S->>SYS: ตรวจสอบสัญญา
    SYS-->>S: ยืนยันสัญญา
    
    S->>C: แสดง Blockchain Address
    C->>BC: โอน Crypto
    BC-->>C: TX Hash
    
    C->>S: แจ้ง TX Hash
    S->>SYS: บันทึก Transaction
    SYS->>EXP: ตรวจสอบ Status
    EXP-->>SYS: PENDING
    
    loop Polling
        SYS->>EXP: ตรวจสอบอีกครั้ง
        EXP-->>SYS: CONFIRMED
    end
    
    SYS->>SYS: อัพเดท Status
    SYS-->>S: ยืนยันการชำระเงิน
    S-->>C: มอบอาหาร
```

## 7. Report Generation Flow

```mermaid
flowchart TD
    START([ผู้จัดการเข้าสู่ระบบ]) --> SELECT{เลือกประเภทรายงาน}
    
    SELECT -->|รายร้านค้า| STORE[สรุปยอดรายร้าน]
    SELECT -->|รายวัน| DAILY[สรุปยอดรายวัน]
    SELECT -->|รายเดือน| MONTHLY[สรุปยอดรายเดือน]
    SELECT -->|รายปี| YEARLY[สรุปยอดรายปี]
    
    STORE --> FILTER1[เลือกร้านและช่วงวันที่]
    DAILY --> FILTER2[เลือกวันที่]
    MONTHLY --> FILTER3[เลือกเดือน]
    YEARLY --> FILTER4[เลือกปี]
    
    FILTER1 --> QUERY[Query Database]
    FILTER2 --> QUERY
    FILTER3 --> QUERY
    FILTER4 --> QUERY
    
    QUERY --> PROCESS[ประมวลผลข้อมูล]
    PROCESS --> GROUP[แยกตาม Payment Method]
    GROUP --> CALC[คำนวณยอดรวม]
    CALC --> FORMAT[จัดรูปแบบรายงาน]
    FORMAT --> DISPLAY[แสดงผล]
    
    DISPLAY --> EXPORT{Export?}
    EXPORT -->|ใช่| EXCEL[Export Excel]
    EXPORT -->|ไม่| END([เสร็จสิ้น])
    EXCEL --> END
```

## 8. Tax Invoice Generation

```mermaid
flowchart LR
    A[Transaction Created] --> B{ต้องการ<br/>ใบกำกับภาษี?}
    
    B -->|ใช่| C[เรียก Tax Service]
    B -->|ไม่| END([ไม่สร้าง])
    
    C --> D[ดึง Payment Method]
    D --> E[คำนวณ VAT 7%]
    E --> F[สร้าง Invoice Number]
    F --> G[บันทึก Tax Invoice]
    
    G --> H{ส่ง E-Tax?}
    H -->|ใช่| I[เรียก E-Tax Provider]
    H -->|ไม่| J[เก็บไว้ในระบบ]
    
    I --> K[ส่งข้อมูลให้สรรพากร]
    K --> L[อัพเดท Status]
    J --> L
    L --> END2([เสร็จสิ้น])
```

## 9. Component Interaction

```mermaid
graph TB
    subgraph "API Endpoints"
        E1[/api/counter/exchange]
        E2[/api/payment-hub/use]
        E3[/api/counter/refund]
        E4[/api/reports/payment/store]
    end
    
    subgraph "Services"
        S1[PaymentHub]
        S2[RefundService]
        S3[ReportService]
    end
    
    subgraph "Models"
        M1[FoodCourtID]
        M2[Transaction]
        M3[Store]
    end
    
    E1 --> S1
    E2 --> S1
    E3 --> S2
    E4 --> S3
    
    S1 --> M1
    S1 --> M2
    S2 --> M1
    S3 --> M2
    S3 --> M3
```

## 10. Security Flow

```mermaid
flowchart TD
    REQ[API Request] --> AUTH{Authentication}
    
    AUTH -->|ไม่ผ่าน| REJECT[Reject Request]
    AUTH -->|ผ่าน| VALIDATE{Validation}
    
    VALIDATE -->|ไม่ผ่าน| ERROR[Return Error]
    VALIDATE -->|ผ่าน| RATE{Rate Limit}
    
    RATE -->|เกิน| THROTTLE[Throttle]
    RATE -->|ไม่เกิน| PROCESS[Process Request]
    
    PROCESS --> AUDIT[Log to Audit Trail]
    AUDIT --> RESPONSE[Return Response]
    
    style AUTH fill:#ffeb3b
    style VALIDATE fill:#ff9800
    style AUDIT fill:#4caf50
```

---

## การใช้งาน Diagrams

Diagrams เหล่านี้ใช้ Mermaid syntax สามารถแสดงผลได้ใน:
- GitHub (รองรับ Mermaid)
- VS Code (ใช้ Mermaid extension)
- Online: https://mermaid.live
- Documentation tools ที่รองรับ Mermaid

