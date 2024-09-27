#include <stdio.h>
#include <string.h>


#include "esp_event.h"
#include "esp_log.h"
#include "esp_system.h"
#include "esp_mac.h"
#include "esp_sleep.h"
#include "esp_random.h"
#include "esp_wifi.h"
#include "freertos/FreeRTOS.h"
#include "freertos/event_groups.h"
#include "lwip/err.h"
#include "lwip/sys.h"
#include "nvs_flash.h"
#include "time.h"
#include <stdlib.h>
#include "lwip/sockets.h" // Para sockets

//Credenciales de WiFi

#define WIFI_SSID "Melisso-ont-2.4g"
#define WIFI_PASSWORD "7dgzqnqNmjw5"
#define SERVER_IP     "192.168.100.203" // IP del servidor
#define SERVER_PORT   1234

// Variables de WiFi
#define WIFI_CONNECTED_BIT BIT0
#define WIFI_FAIL_BIT BIT1
static const char* TAG = "WIFI";
static int s_retry_num = 0;
static EventGroupHandle_t s_wifi_event_group;


void event_handler(void* arg, esp_event_base_t event_base,
                          int32_t event_id, void* event_data) {
    if (event_base == WIFI_EVENT && event_id == WIFI_EVENT_STA_START) {
        esp_wifi_connect();
    } else if (event_base == WIFI_EVENT &&
               event_id == WIFI_EVENT_STA_DISCONNECTED) {
        if (s_retry_num < 10) {
            esp_wifi_connect();
            s_retry_num++;
            ESP_LOGI(TAG, "retry to connect to the AP");
        } else {
            xEventGroupSetBits(s_wifi_event_group, WIFI_FAIL_BIT);
        }
        ESP_LOGI(TAG, "connect to the AP fail");
    } else if (event_base == IP_EVENT && event_id == IP_EVENT_STA_GOT_IP) {
        ip_event_got_ip_t* event = (ip_event_got_ip_t*)event_data;
        ESP_LOGI(TAG, "got ip:" IPSTR, IP2STR(&event->ip_info.ip));
        s_retry_num = 0;
        xEventGroupSetBits(s_wifi_event_group, WIFI_CONNECTED_BIT);
    }
}

void wifi_init_sta(char* ssid, char* password) {
    s_wifi_event_group = xEventGroupCreate();

    ESP_ERROR_CHECK(esp_netif_init());

    ESP_ERROR_CHECK(esp_event_loop_create_default());
    esp_netif_create_default_wifi_sta();

    wifi_init_config_t cfg = WIFI_INIT_CONFIG_DEFAULT();
    ESP_ERROR_CHECK(esp_wifi_init(&cfg));

    esp_event_handler_instance_t instance_any_id;
    esp_event_handler_instance_t instance_got_ip;
    ESP_ERROR_CHECK(esp_event_handler_instance_register(
        WIFI_EVENT, ESP_EVENT_ANY_ID, &event_handler, NULL, &instance_any_id));
    ESP_ERROR_CHECK(esp_event_handler_instance_register(
        IP_EVENT, IP_EVENT_STA_GOT_IP, &event_handler, NULL, &instance_got_ip));

    wifi_config_t wifi_config;
    memset(&wifi_config, 0, sizeof(wifi_config_t));

    // Set the specific fields
    strcpy((char*)wifi_config.sta.ssid, WIFI_SSID);
    strcpy((char*)wifi_config.sta.password, WIFI_PASSWORD);
    wifi_config.sta.threshold.authmode = WIFI_AUTH_WPA2_PSK;
    wifi_config.sta.pmf_cfg.capable = true;
    wifi_config.sta.pmf_cfg.required = false;
    ESP_ERROR_CHECK(esp_wifi_set_mode(WIFI_MODE_STA));
    ESP_ERROR_CHECK(esp_wifi_set_config(WIFI_IF_STA, &wifi_config));
    ESP_ERROR_CHECK(esp_wifi_start());

    ESP_LOGI(TAG, "wifi_init_sta finished.");

    EventBits_t bits = xEventGroupWaitBits(s_wifi_event_group,
                                           WIFI_CONNECTED_BIT | WIFI_FAIL_BIT,
                                           pdFALSE, pdFALSE, portMAX_DELAY);

    if (bits & WIFI_CONNECTED_BIT) {
        ESP_LOGI(TAG, "connected to ap SSID:%s password:%s", ssid,
                 password);
    } else if (bits & WIFI_FAIL_BIT) {
        ESP_LOGI(TAG, "Failed to connect to SSID:%s, password:%s", ssid,
                 password);
    } else {
        ESP_LOGE(TAG, "UNEXPECTED EVENT");
    }

    ESP_ERROR_CHECK(esp_event_handler_instance_unregister(
        IP_EVENT, IP_EVENT_STA_GOT_IP, instance_got_ip));
    ESP_ERROR_CHECK(esp_event_handler_instance_unregister(
        WIFI_EVENT, ESP_EVENT_ANY_ID, instance_any_id));
    vEventGroupDelete(s_wifi_event_group);
}

void nvs_init() {
    esp_err_t ret = nvs_flash_init();
    if (ret == ESP_ERR_NVS_NO_FREE_PAGES ||
        ret == ESP_ERR_NVS_NEW_VERSION_FOUND) {
        ESP_ERROR_CHECK(nvs_flash_erase());
        ret = nvs_flash_init();
    }
    ESP_ERROR_CHECK(ret);
}

char* create_packet(char protocol) {
    char transport_layer;

    // 
    unsigned short packet_size;

    switch(protocol) {
        case 0:
            packet_size = 16;
            break;
        case 1:
            packet_size = 17;
            break;
        case 2:
            packet_size = 27;
            break;
        case 3:
            packet_size = 55;
            break;
        case 4:
            packet_size = 48027;
            break;
    }

    char* buffer = malloc(packet_size);


    // HEADER 
    // Device Mac
    int pointer = 0;
    // PENDIENTE: cambiar esto por la mac real
    char mac[6] = {7,6,5,4,3,4};
    memcpy(&buffer[pointer], &mac, 6);
    pointer += 6;
    // Msg ID
    short msgID = 259;
    memcpy(&buffer[pointer], &msgID, sizeof(msgID));
    pointer += sizeof(msgID);

    // Protocol ID
    memcpy(&buffer[pointer], &protocol, sizeof(protocol));
    pointer += sizeof(protocol);
    // strcpy(protocol_id, ((char*) protocol));

    //transport layer (wip)
    transport_layer = 0;
    memcpy(&buffer[pointer], &transport_layer, sizeof(transport_layer));
    pointer+= sizeof(transport_layer);

    // length
    memcpy(&buffer[pointer], &packet_size, sizeof(packet_size));
    pointer+= sizeof(packet_size);

    // BODY

    // timestamp
    if (protocol >= 0) { // P0-P4 envian timestamp
        unsigned int timestamp = time(NULL);
        memcpy(&buffer[pointer], &timestamp, 4);
        pointer += 4;   
    }
    // battery (batt_level)
    if (protocol >= 1) { // P1-P4 envían batt_level
        unsigned int random_num = esp_random() % 101;
        ESP_LOGI("PKT","Battery Level: %i", random_num);
        memcpy(&buffer[pointer], &random_num, 1);
        pointer += 1;
    }
    
    // temp, pres, hum, co
    if (protocol >= 2) { // P2-P4 envían temp, pres, hum, co
        unsigned int random_temp  = 5 + (esp_random() % 26);
        unsigned int random_pres  = 1000 + (esp_random() % 201);
        unsigned int random_hum = 30 +  (esp_random() % 51);
        float random_co = 30 + ((float)170)*((float) esp_random()/(float) UINT_MAX);

        memcpy(&buffer[pointer], &random_temp, 1);
        pointer+=1;
        memcpy(&buffer[pointer], &random_pres, 4);
        pointer+=4;
        memcpy(&buffer[pointer], &random_hum, 1);
        pointer+=1;
        memcpy(&buffer[pointer], &random_co, 4);
        pointer+=4;
    
    }




    ESP_LOGI("PKT", "PACKET SIZE:  %hu", packet_size);
    ESP_LOGI("PKT", "Buffer creado");

    return buffer;
}

/* === antiguos ===
// char* create_packet_0() {
//     // Get MAC Adress
//     char* mac = "0";
//     // Random id
//     char* id = "0";
//     // Header
//     char* header = strcat(mac, id);
//     // Header + Protocol + Transport + Length
//     header = strcat(header, "0016");
//     // Done
    
//     // Body
//     // timestamp
//     char* body = "0000";

//     //Join message
//     char* packet = strcat(header, body);
//     return packet;
// }

// char* create_packet_1() {
//     // Get MAC Adress
//     char* mac = "0";
//     // Random id
//     char* id = "0";
//     // Protocol Transport Length
//     char* protocol_transport_length = "0017";
//     // Calculate header size to avoid overflowing memwrite
//     size_t header_size = strlen(mac) + strlen(id) + strlen(protocol_transport_length) + 1; // ends on \0 ?
    
//     // Header
//     char* header = (char*) malloc(header_size);
//     strcpy(header,mac);
//     strcat(header,id);
//     strcat(header,protocol_transport_length);
//     // Header + Protocol + Transport + Length
//     // char* header = strcat(mac, id);
//     // header = strcat(header, "0017");
//     // Done
    
//     // Body
//     // timestamp
//     char* body = "0000";
//     // batt level
//     body = strcat(body, "0");

//     //Join message
//     char* packet = strcat(header, body);
//     return packet;

// }

// char* create_packet_2() {
//     // Get MAC Adress
//     char* mac = "0";
//     // Random id
//     char* id = "0";
//     // Header
//     char* header = strcat(mac, id);
//     // Header + Protocol + Transport + Length
//     header = strcat(header, "0027");
//     // Done
    
//     // Body
//     // timestamp
//     char* body = "0000";
//     // batt level
//     body = strcat(body, "0");
//     // temp
//     body = strcat(body, "0");
//     // press
//     body = strcat(body, "0");
//     // hum
//     body = strcat(body, "0");
//     // co
//     body = strcat(body, "0");

//     //Join message
//     char* packet = strcat(header, body);
//     return packet;

// }

//TBD
// char* create_packet_3() {}

//TBD
// char* create_packet_4() {}
*/


int socket_tcp(){
    struct sockaddr_in server_addr;
    server_addr.sin_family = AF_INET;
    server_addr.sin_port = htons(SERVER_PORT);
    inet_pton(AF_INET, SERVER_IP, &server_addr.sin_addr.s_addr);

    // Crear un socket
    int sock = socket(AF_INET, SOCK_STREAM, IPPROTO_TCP);
    if (sock < 0) {
        ESP_LOGE(TAG, "Error al crear el socket");
        return 1;
    }

    // Conectar al servidor
    if (connect(sock, (struct sockaddr *)&server_addr, sizeof(server_addr)) != 0) {
        ESP_LOGE(TAG, "Error al conectar");
        close(sock);
        return 1;
    }

    return sock;
}

void close_tcp(int socket) {
    // Cerrar el socket
    close(socket);
}

char* config_conn(int socket, char* ptr_buffer) {
    // Pedir protocolo
    char* config = "CONFIG";
    send(socket, config, strlen(config), 0);

    // Recibir respuesta
    // char rx_buffer[128];
    int rx_len = recv(socket, ptr_buffer, sizeof(ptr_buffer) - 1, 0);
    if (rx_len < 0) {
        ESP_LOGE(TAG, "Error al recibir datos");
        exit(1);
    }
    ESP_LOGI(TAG, "Datos recibidos: %s", ptr_buffer);

    return ptr_buffer;
}

void print_bytes(char*  buffer, int size) {
    ESP_LOGI("DEBUG","=== BUFFER PRINTING ===");
    for (int i=0; i<size;i++) {

        ESP_LOGI("DEBUG", "[%i] %c", i, buffer[i]);
    }
    ESP_LOGI("DEBUG", "=== BUFFER END ===");
}


void send_data(int socket, char* conf_data) {
    char* send_ack = "PACKAGE";
    send(socket, send_ack, strlen(send_ack), 0);
    // ESP_LOGI(TAG, "Recibido conf_data\n");
    ESP_LOGI(TAG, "Conf_Data: %s\n", conf_data);
    ESP_LOGI(TAG, "%c", conf_data[0]);
    ESP_LOGI(TAG, "%c", conf_data[1]);
    ESP_LOGI(TAG, "%c", conf_data[2]);


    // Chequeo de protocolo (y capa de transporte a futuro), para luego enviar datos
    // Como el mensaje enviado es un string codificado en UTF-8 es necesario truncar los primeros dos carácteres
    char conf_flag[3] = {conf_data[0], conf_data[1], '\0'};

    ESP_LOGI(TAG, "Conf_Flag: %s", conf_flag);

    int protocol = 0;
    if (strcmp(conf_flag, "00") == 0) protocol=0;
    if (strcmp(conf_flag, "10") == 0) protocol=1;
    if (strcmp(conf_flag, "20") == 0) protocol=2;
    if (strcmp(conf_flag, "30") == 0) protocol=3;
    if (strcmp(conf_flag, "40") == 0) protocol=4;



    ESP_LOGI(TAG,"Usando protocolo %i\n", protocol);
    char* pack = create_packet(protocol);
    unsigned short packet_size;
    memcpy(&packet_size, &pack[10], 2);
    ESP_LOGI(TAG, "packet_size %i", packet_size);
    send(socket, pack, packet_size, 0);
    free(pack);

    // else {
    //     //error
    //     ESP_LOGI(TAG,"Mensaje invalido\n");
    // }
    
}



void app_main(void){
    //añadir loop de SLEEP
    nvs_init();

    ESP_LOGI(TAG, "float random %f",  (float) esp_random()/(float) UINT_MAX);

        
    wifi_init_sta(WIFI_SSID, WIFI_PASSWORD);
    ESP_LOGI(TAG,"Conectado a WiFi!\n");
    int sock = socket_tcp();
    ESP_LOGI(TAG,"Conectado al socket\n");
    char conf_data[128];
    config_conn(sock, conf_data);
    ESP_LOGI(TAG,"Configuracion lista, enviando datos\n");
    ESP_LOGI(TAG,"DEBUG\n");
    ESP_LOGI(TAG,"Configuración: %s\n", conf_data);
    ESP_LOGI(TAG,"DEBUG 2\n");
    send_data(sock, conf_data);
    ESP_LOGI(TAG,"A mimir\n");
    close_tcp(sock);
    //Deep Sleep for one second
    esp_deep_sleep(1000000);
}
