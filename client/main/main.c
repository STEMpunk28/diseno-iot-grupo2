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
#include "math.h"
#include <unistd.h>
#include "lwip/sockets.h" // Para sockets

//Credenciales de WiFi

#define WIFI_SSID "Melisso-ont-2.4g" // "RASPI"
#define WIFI_PASSWORD "7dgzqnqNmjw5" // "123456789"
#define SERVER_IP     "192.168.100.203" // "10.20.1.1" // IP del servidor
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

char* create_packet(char protocol, char transport) {
    ESP_LOGI("DEBUG", "CREATE PACKET --");
    char transport_layer;
    unsigned short packet_size;

    switch(protocol) {
        case 0+'0':
            ESP_LOGI(TAG, "packet 16");
            packet_size = 16;
            break;
        case 1+'0':
            ESP_LOGI(TAG, "packet 17");
            packet_size = 17;
            break;
        case 2+'0':
            ESP_LOGI(TAG, "packet 27");
            packet_size = 27;
            break;
        case 3+'0':
            ESP_LOGI(TAG, "packet 55");
            packet_size = 55;
            break;
        case 4+'0':
            ESP_LOGI(TAG, "packet 48027");
            packet_size = 48027;
            break;
    }

    char* buffer = malloc(packet_size);

    // HEADER 
    // Device Mac
    int pointer = 0;

    uint8_t baseMac[6];
    // Get MAC address of the WiFi station interface
    esp_read_mac(baseMac, ESP_MAC_WIFI_STA);

    // char mac[6] = {7,6,5,4,3,4};
    memcpy(&buffer[pointer], &baseMac, 6);
    pointer += 6;
    
    // Msg ID
    unsigned int msg_ID = esp_random();
    memcpy(&buffer[pointer], &msg_ID, 2);
    pointer += 2;

    // Protocol ID
    memcpy(&buffer[pointer], &protocol, sizeof(protocol));
    pointer += sizeof(protocol);

    //transport layer (wip)
    transport_layer = transport;
    memcpy(&buffer[pointer], &transport_layer, sizeof(transport_layer));
    pointer+= sizeof(transport_layer);

    ESP_LOGI("PKT", "TRANSPORT LAYER WRITTEN");

    // length
    memcpy(&buffer[pointer], &packet_size, sizeof(packet_size));
    pointer+= sizeof(packet_size);

    // BODY

    // timestamp
    if (protocol >= 0+'0') { // P0-P4 envian timestamp
        ESP_LOGI("PKT", "PROTOCOL 0 WRITTEN");
        unsigned int timestamp = time(NULL);
        memcpy(&buffer[pointer], &timestamp, 4);
        pointer += 4;
    }
    // battery (batt_level)
    if (protocol >= 1+'0') { // P1-P4 envían batt_level
        ESP_LOGI("PKT", "PROTOCOL 1 WRITTEN");
        unsigned int random_num = esp_random() % 101;
        ESP_LOGI("PKT","Battery Level: %i", random_num);
        memcpy(&buffer[pointer], &random_num, 1);
        pointer += 1;
    }
    
    // temp, pres, hum, co
    if (protocol >= 2+'0') { // P2-P4 envían temp, pres, hum, co
        ESP_LOGI("PKT", "PROTOCOL 2 WRITTEN");
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

    if (protocol == 3+'0') { // Solo p3 envia amp, fre y rms
        ESP_LOGI("PKT", "PROTOCOL 3 WRITTEN");
        float random_amp_x = 30 + ((float)170)*((float) esp_random()/(float) UINT_MAX);
        float random_amp_y = 30 + ((float)170)*((float) esp_random()/(float) UINT_MAX);
        float random_amp_z = 30 + ((float)170)*((float) esp_random()/(float) UINT_MAX);
        float random_fre_x = 30 + ((float)170)*((float) esp_random()/(float) UINT_MAX);
        float random_fre_y = 30 + ((float)170)*((float) esp_random()/(float) UINT_MAX);
        float random_fre_z = 30 + ((float)170)*((float) esp_random()/(float) UINT_MAX);

        memcpy(&buffer[pointer], &random_amp_x, 4);
        pointer+=4;
        memcpy(&buffer[pointer], &random_amp_y, 4);
        pointer+=4;
        memcpy(&buffer[pointer], &random_amp_z, 4);
        pointer+=4;
        memcpy(&buffer[pointer], &random_fre_x, 4);
        pointer+=4;
        memcpy(&buffer[pointer], &random_fre_y, 4);
        pointer+=4;
        memcpy(&buffer[pointer], &random_fre_z, 4);
        pointer+=4;
    
    }

    if (protocol == 4+'0') { // Solo p4 envia acc y gyr        
        ESP_LOGI("PKT", "PROTOCOL 4 WRITTEN");
        // acc_x from -1000.0 to 1000.0
        for (int i = 0; i < 2000; i++) {
            float random_acc = -16 + ((float)32)*((float) esp_random()/(float) UINT_MAX);
            memcpy(&buffer[pointer], &random_acc, 4);
            pointer+=4;
        }
        // acc_y from -1000.0 to 1000.0
        for (int i = 0; i < 2000; i++) {
            float random_acc = -16 + ((float)32)*((float) esp_random()/(float) UINT_MAX);
            memcpy(&buffer[pointer], &random_acc, 4);
            pointer+=4;
        }
        // acc_z from -1000.0 to 1000.0
        for (int i = 0; i < 2000; i++) {
            float random_acc = -16 + ((float)32)*((float) esp_random()/(float) UINT_MAX);
            memcpy(&buffer[pointer], &random_acc, 4);
            pointer+=4;
        }
        // gyr_x from -1000.0 to 1000.0
        for (int i = 0; i < 2000; i++) {
            float random_acc = -16 + ((float)32)*((float) esp_random()/(float) UINT_MAX);
            memcpy(&buffer[pointer], &random_acc, 4);
            pointer+=4;
        }
        // gyr_y from -1000.0 to 1000.0
        for (int i = 0; i < 2000; i++) {
            float random_acc = -16 + ((float)32)*((float) esp_random()/(float) UINT_MAX);
            memcpy(&buffer[pointer], &random_acc, 4);
            pointer+=4;
        }
        // gyr_z from -1000.0 to 1000.0
        for (int i = 0; i < 2000; i++) {
            float random_acc = -16 + ((float)32)*((float) esp_random()/(float) UINT_MAX);
            memcpy(&buffer[pointer], &random_acc, 4);
            pointer+=4;
        }
    }

    ESP_LOGI("PKT", "PACKET SIZE:  %hu", packet_size);
    ESP_LOGI("PKT", "Buffer creado");

    return buffer;
}


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
    int rx_len = recv(socket, ptr_buffer, sizeof(ptr_buffer) - 1, 0);
    if (rx_len < 0) {
        ESP_LOGE(TAG, "Error al recibir datos");
        exit(1);
    }
    ESP_LOGI(TAG, "Configuracion recibida: %s", ptr_buffer);

    return ptr_buffer;
}

void print_bytes(char*  buffer, int size) {
    ESP_LOGI("DEBUG","=== BUFFER PRINTING ===");
    for (int i=0; i<size;i++) {
        ESP_LOGI("DEBUG", "[%i] %c", i, buffer[i]);
    }
    ESP_LOGI("DEBUG", "=== BUFFER END ===");
}


void send_data(int socket, char protocol, char transport) {
    ESP_LOGI("DEBUG", "SEND_DATA --");
    char* send_ack = "PACKAGE";
    send(socket, send_ack, strlen(send_ack), 0);

    ESP_LOGI(TAG,"Usando protocolo %c\n", protocol);
    char* pack = create_packet(protocol, transport);
    unsigned short packet_size;
    memcpy(&packet_size, &pack[10], 2);
    sleep(1);
    ESP_LOGI(TAG, "packet_size %i", packet_size);

    int MAX_PACKET_SIZE = 750;

    if (packet_size < MAX_PACKET_SIZE) {
        send(socket, pack, packet_size, 0);
        sleep(1);
    } else {

        int init = 0;
        while (init < packet_size-1) {
            ESP_LOGI(TAG, "sending %i/%i ...", init, packet_size);
            int size = fmin(MAX_PACKET_SIZE, packet_size-init);
            send(socket, pack + init, size, 0);
            init += size;
            // sleep(1);
        }



    }
    free(pack);
    
}



void app_main(void){
    nvs_init();
    ESP_LOGI(TAG, "float random %f",  (float) esp_random()/(float) UINT_MAX);
        
    wifi_init_sta(WIFI_SSID, WIFI_PASSWORD);
    ESP_LOGI(TAG,"Conectado a WiFi!\n");
    int sock = socket_tcp();
    ESP_LOGI(TAG,"Conectado al socket\n");
    char conf_data[128];
    config_conn(sock, conf_data);
    ESP_LOGI(TAG,"Configuracion lista, enviando datos\n");
    
    ESP_LOGI(TAG, "Conf_Data: %s\n", conf_data);
    char protocol = conf_data[0];
    ESP_LOGI(TAG, "Protocolo: %c\n", protocol);
    char layer = conf_data[1];
    ESP_LOGI(TAG, "Capa de transporte: %c\n", layer);

    ESP_LOGI(TAG,"DEBUG\n");
    // Guardar la capa de transporte para configurar la conexion    
    send_data(sock, protocol, layer);
    
    
    
    
    
    if (layer == 0+'0') {
        ESP_LOGI(TAG,"TCP, A mimir\n");
        //Deep Sleep for one second
        esp_deep_sleep(1000000);
    }
    if (layer == 1+'0') {
        ESP_LOGI(TAG,"UDP, espero un segundo y sigo enviando\n");
        vTaskDelay(1000/portTICK_PERIOD_MS);
    }
        
}
