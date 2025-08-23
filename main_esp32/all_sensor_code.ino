#define seed_sow_servo 33

Servo seedSowServo;

int seed_sow_state = 0;

const char* ssid = "Wifi abar ki jinis";
const char* password = "passdemunah!";
const char* serverName = "https://agri-bot-kwis.onrender.com/esp32-receive/"; 


void setup() {
  
  Serial.begin(115200);

  WiFi.begin(ssid, password);
  Serial.print("Connecting to WiFi");
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("\nConnected to WiFi");

  seedSowServo.attach(seed_sow_servo);

  seedSowServo.write(90);
}


String response = "";
String previous_response = response;


void loop() {


  
  if (WiFi.status() == WL_CONNECTED) {
    HTTPClient http;

    http.begin(serverName);          
    int httpResponseCode = http.GET(); 

    if (httpResponseCode > 0) {
      Serial.print("Response code: ");
      Serial.println(httpResponseCode);

      previous_response = response;
      response = http.getString(); 
      Serial.println("Server response:");
      Serial.println(response); 
    } else {
      Serial.print("Error code: ");
      Serial.println(httpResponseCode);
    }

    http.end();

    
    if (response == "seed_sow_on"){
       seedSowServo.write(180);
       delay(1000);
    }
    if (response == "seed_sow_off"){
       seedSowServo.write(0);
       delay(1000);
    }
    }
  
    }
    