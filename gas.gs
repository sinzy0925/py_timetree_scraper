/**
 * 12時間表記(AM/PM)の時刻文字列をパースして、Dateオブジェクトを生成するヘルパー関数
 * @param {string} dateStr - "YYYY-MM-DD"形式の日付文字列
 * @param {string} timeStr - "H:MM AM/PM"形式の時刻文字列
 * @returns {Date}
 */
function parseDateTime(dateStr, timeStr) {
  const dateParts = dateStr.split('-');
  const year = parseInt(dateParts[0], 10);
  const month = parseInt(dateParts[1], 10) - 1; // 月は0-indexed
  const day = parseInt(dateParts[2], 10);

  const timeMatch = timeStr.match(/(\d+):(\d+)\s(AM|PM)/);
  let hour = parseInt(timeMatch[1], 10);
  const minute = parseInt(timeMatch[2], 10);
  const ampm = timeMatch[3];

  if (ampm === 'PM' && hour < 12) {
    hour += 12;
  }
  if (ampm === 'AM' && hour === 12) { // 深夜12時(12:00 AM)のケース
    hour = 0;
  }

  return new Date(year, month, day, hour, minute);
}

/**
 * WebアプリとしてPOSTリクエストを受け取ったときに実行されるメイン関数
 * @param {Object} e - POSTリクエストのイベントオブジェクト
 */
function doPost(e) {
  const logs = []; // Pythonに返すためのログ収集用配列
  let statusMessage = "";

  try {
    const events = JSON.parse(e.postData.contents);
    const calendar = CalendarApp.getDefaultCalendar();
    
    logs.push(`Received ${events.length} events to process.`);

    events.forEach(eventData => {
      const title = eventData.title;
      const dateStr = eventData.date;
      const timeStr = eventData.time;

      logs.push(`Processing: '${title}' on ${dateStr} at ${timeStr || 'All-day'}`);

      if (timeStr) {
        // 時間指定イベント
        const startTime = parseDateTime(dateStr, timeStr);
        const endTime = new Date(startTime.getTime() + (60 * 60 * 1000)); // 仮に1時間後
        
        logs.push(` -> Creating timed event. Start: ${startTime}, End: ${endTime}`);
        calendar.createEvent(title, startTime, endTime);
        
      } else {
        // 終日イベント
        const eventDate = new Date(dateStr);
        // タイムゾーン問題を避けるため、UTCで日付を扱う
        const utcDate = new Date(eventDate.getUTCFullYear(), eventDate.getUTCMonth(), eventDate.getUTCDate());

        logs.push(` -> Creating all-day event on: ${utcDate}`);
        calendar.createAllDayEvent(title, utcDate);
      }
    });
    
    statusMessage = "Successfully processed " + events.length + " events.";
    logs.push(statusMessage);
    
  } catch (error) {
    statusMessage = "Error processing request: " + error.toString();
    logs.push(statusMessage);
    logs.push("Received data: " + e.postData.contents);
  }
  
  // 処理結果のステータスと、収集したログをまとめてJSONで返す
  return ContentService
    .createTextOutput(JSON.stringify({ 
        status: statusMessage,
        logs: logs 
    }))
    .setMimeType(ContentService.MimeType.JSON);
}