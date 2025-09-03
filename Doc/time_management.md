3. Time Management (/api/v1/inverter/time) ✅ Complete

## 3.1 Get Current Time ✅ Complete
- Legacy Command: T
- HTTP Method: GET
- Endpoint: /api/v1/inverter/time/current
- Raw Command: ^P004T<CRC><cr>
- Raw Response: ^D017YYYYMMDDHHMMSS<CRC><cr>
- Response:
  ```json
  {
    "datetime": "2024-08-31T18:30:45",
    "year": 2024,
    "month": 8,
    "day": 31,
    "hour": 18,
    "minute": 30,
    "second": 45,
    "timestamp": "2025-09-03T12:21:43.279Z"
  }
  ```

## 3.2 Set Date Time ✅ Complete
- Legacy Command: DAT
- HTTP Method: PUT
- Endpoint: /api/v1/inverter/time/current
- Raw Command: ^S018DATyymmddhhffss<cr>
- Request Body:
  ```json
  {
    "datetime": "2024-08-31T18:30:45"
  }
  ```
- Response:
  ```json
  {
    "status": "success",
    "datetime": "2024-08-31T18:30:45",
    "timestamp": "2025-09-03T12:21:43.279Z"
  }
  ```

## 3.3 Get AC Charge Time Bucket ✅ Complete
- Legacy Command: ACCT
- HTTP Method: GET
- Endpoint: /api/v1/inverter/time/charge-schedule
- Raw Command: ^P007ACCT<CRC><cr>
- Raw Response: ^D008HHMMHHMME<CRC><cr> (HH=hour, MM=minute, E=enabled)
- Response:
  ```json
  {
    "start_time": "00:00",
    "end_time": "23:59",
    "enabled": true,
    "timestamp": "2025-09-03T12:21:43.279Z"
  }
  ```

## 3.4 Get AC Load Time Bucket ✅ Complete
- Legacy Command: ACLT
- HTTP Method: GET
- Endpoint: /api/v1/inverter/time/load-schedule
- Raw Command: ^P007ACLT<CRC><cr>
- Raw Response: ^D008HHMMHHMME<CRC><cr> (HH=hour, MM=minute, E=enabled)
- Response:
  ```json
  {
    "start_time": "00:00",
    "end_time": "23:59",
    "enabled": true,
    "timestamp": "2025-09-03T12:21:43.279Z"
  }
  ```