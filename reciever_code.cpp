#define __STDC_FORMAT_MACROS 1
#include <inttypes.h>


// HackRF lib
#include <libhackrf/hackrf.h>
// Normal system libs
#include <stdio.h>
#include <stdlib.h>
#include <stdbool.h>
#include <unistd.h>
#include <inttypes.h>
#include <math.h>
#include <signal.h>
#include <string>
#include <cstring>
#include <ctime>
#include <chrono>
#include <thread>
#include <iostream>
#include <time.h>
#include <math.h>
#include <fstream>
#include <fftw3.h>

using namespace std;
//
volatile bool do_exit = false;// flag : stop recieve



// callcback variables
int blocks_val;
int block_cnt = 0;
FILE *fp;
FILE *fst;
FILE *fet;
string fileName = "";
string filePrefix;
string folder = "";
int fileCnt = 1;
bool do_switch = false;
bool need_write = false;
int attrf = 0;
string sname;
string ename;

uint8_t buf[262144];
int rx_callback(hackrf_transfer* transfer)
{
    if (do_exit){
		block_cnt = 0;
		fileCnt = 1;
        return 0;
    }

    for (int i = 0; i < 262144; i++){
        buf[i] = transfer->buffer[i];
    }

	if (need_write){
		if(block_cnt == blocks_val){
			//printf("окончание записи в файл\n\n");
			
			auto mt2 = std::chrono::high_resolution_clock::now();
			auto m2 = mt2.time_since_epoch();
			long long int t2 = m2.count();
			fet = fopen(ename.c_str(),"a");
			fprintf(fet,"%llu\n",t2);
			fclose(fet);
			
			block_cnt = 0;
		}

		if(block_cnt == 0){ // создание нового файла
			if(fp != NULL) fclose(fp);
			fileName = folder + filePrefix + "power" + std::to_string(fileCnt) + ".bin";
			fileCnt = fileCnt + 1;
			if(need_write){
				fp = fopen(fileName.c_str(),"w");
			}
		}
		if(need_write){
			fwrite(transfer->buffer, transfer->valid_length, 1, fp); // запись в файл
		}
			
		if(block_cnt == 0){ // переключение аттенюатора (здесь через флаг, команда переключения в другом потоке)
			
			
			auto mt2 = std::chrono::high_resolution_clock::now();
			auto m2 = mt2.time_since_epoch();
			long long int t2 = m2.count();
			if(need_write){
				fst = fopen(sname.c_str(),"a");
				fprintf(fst,"%llu\n",t2);
				fclose(fst);
			}
			
		} 
		
		block_cnt = block_cnt + 1;
		//cout << block_cnt << "/" << blocks_val << '\n';
	}
		
    return 0;
}

///////////////
double calculateSampleRate(double desired_sample_rate_hz){
    if(desired_sample_rate_hz <= 262144 * 4)
        return 262144 * 4;
    if(desired_sample_rate_hz <= 262144 * 8)
        return 262144 * 8;
    if(desired_sample_rate_hz <= 262144 * 16)
        return 262144 * 16;
    if(desired_sample_rate_hz <= 262144 * 32)
        return 262144 * 32;
    return 262144 * 32;
}
//////////////
bool isTerminateSignal = false;
void my_handler(int s){
    printf("\nStop signal %d\n",s);
    //set rf gain
    do_exit = true;
    isTerminateSignal = true;
}
int  set_open_device(const char* const desired_serial_number, hackrf_device** device){
    // подготовка нужного приёмника к началу работы с приёмником
    int result = hackrf_open_by_serial(desired_serial_number, device);

    if( result != 0 )
    {
        printf("hackrf_open() failed: (%d)\n", result);
        return 1;
    } else {
        fprintf(stderr, "\nПРИЁМНИК ОБНАРУЖЕН\n");
    }
    return 0;
}

int  set_params(hackrf_device* device,
                uint64_t freq_hz,
                double desired_sample_rate_hz,
                const uint32_t lna_gain_db,
                const uint32_t vga_gain_db,
                uint8_t rf_gain_on_off){

    const double sample_rate_hz = calculateSampleRate(desired_sample_rate_hz);

	fprintf(stderr, " Установлены следующие параметры для приёмника:\n");
    //отключение питания антенны
    int result = hackrf_set_antenna_enable(device, 0);
    if( result != 0 )
    {
        printf("hackrf_set_antenna_enable failed: (%d)\n", result);
        return 1;

    } else {
        fprintf(stderr, "  питание антенны отключено\n");
    }
    /////////////////////////

    //установка частоты приёма
    result = hackrf_set_freq(device, freq_hz);
    if ( result != 0 )
    {
        printf("hackrf_set_freq() failed: (%d)\n", result);
        return 1;
    } else {
        printf("  частота приёмника %" PRIu64 " Гц\n", freq_hz);
    }
    /////////////////

    //установка частоты выборок (количества выборок/с)
    result = hackrf_set_sample_rate(device, sample_rate_hz);
    if( result != 0 ) {
        fprintf(stderr, "hackrf_sample_rate_set() failed: (%d)\n", result);
        return 1;
    } else {
        fprintf(stderr, "  частота выборок %1.0f Гц\n", sample_rate_hz);
    }
    //////////////////

    //расчёт частоты фильтра основной полосы частот
    const uint32_t new_baseband_hz = hackrf_compute_baseband_filter_bw_round_down_lt(sample_rate_hz);
    fprintf(stderr, "  расчитанная ширина полосы %u Гц\n", new_baseband_hz);
    //////////////////
    //установка фильтра полосы частот
    const uint32_t baseband_hz = new_baseband_hz;
    result = hackrf_set_baseband_filter_bandwidth(device,baseband_hz);
    if(result != 0)
    {
        fprintf(stderr, " hackrf_set_baseband() failed: (%d)\n", result);
        return 1;
    } else {
        fprintf(stderr, "  установлена ширина полосы %u Гц\n", baseband_hz);
    }
    //////////////

    //установка усиления ПЧ
    result = hackrf_set_lna_gain(device,lna_gain_db);
    if(result != 0)
    {
        fprintf(stderr, " hackrf_set_lna_gain() failed: (%d)\n", result);
        return 1;
    } else {
        fprintf(stderr, "  ПЧ усиление %u дБ\n", lna_gain_db);
    }
    //////////////

    //установка усиления на видео частоте
    result = hackrf_set_vga_gain(device,vga_gain_db);
    if(result != 0)
    {
        fprintf(stderr, " hackrf_set_vga_gain() failed: (%d)\n", result);
        return 1;
    } else {
        fprintf(stderr, "  видео усиление %u дБ\n", vga_gain_db);
    }
    //////////////

    //установка ВЧ усиления
    result = hackrf_set_amp_enable(device, rf_gain_on_off);
    if(result != 0)
    {
        fprintf(stderr, " hackrf_set_amp_enable() failed: (%d)\n", result);
        return 1;
    } else {
        if(rf_gain_on_off == 1){
            fprintf(stderr, "  включено усиление на 12 дБ\n");
        }else{
            fprintf(stderr, "  входной усилитель выключен\n");
        }
    }
    /////////////
    return result;
}

void show_devices(){
    int result = hackrf_init();
    hackrf_device* device = NULL;
    result = hackrf_open(&device);
    if (result == HACKRF_SUCCESS){
        cout << "some devices detected\n";

        hackrf_device_list_t* devices = hackrf_device_list();

        for(int i = 0; i < devices->devicecount; i++){

            cout << "receiever "<<i + 1<<" - " << devices->serial_numbers[i] << "\n";
        }

    } else {
        cout << "not ok";
    }
}


float task_fft(uint8_t *buf_copy, float f,  float band_width, double sample_rate_hz, int N){
    int a = 0;
    fftw_complex in[N], out[N];
    fftw_plan p;
    float freqs[N];
    float shI[N];
    float shQ[N];
    float P[N];
    float in_real[N];
    float in_imag[N];

    string iq_name;
    float sdf = sample_rate_hz/N;
    float f0 = f;
    float f1 = f0 - band_width/2;
    float f2 = f0 + band_width/2;

    int fi1 = -1;
    int fi2 = -1;
    for(int i = 0; i < N; i++){
        freqs[i] = -sample_rate_hz/2 + sdf*i;
        if(fi1 == -1){
            if(f1 < freqs[i]){
                //printf("%f %f\n",f1,freqs[i]);
                fi1 = i;
            }
        }
        if(fi2 == -1){
            if(f2 < freqs[i]){
                fi2 = i;
            }
        }

    }


    int k = 0;
    for(int j = 0; j < N*2; j++){
        if(j%2 == 0){
            in[k][0] = (float)((int8_t)buf_copy[j])/127;
            in_real[k] = in[k][0];
        } else {
            in[k][1] = (float)((int8_t)buf_copy[j])/127;
            in_imag[k] = in[k][0];
            k = k + 1;
        }
    }

    p = fftw_plan_dft_1d(N, in, out, FFTW_FORWARD, FFTW_ESTIMATE);
    fftw_execute(p);
    fftw_destroy_plan(p);

    for(int j = 0; j < N/2; j++){
        shI[j] = out[j + N/2+1][0];
        shQ[j] = out[j + N/2+1][1];
    }
    for(int j = N/2+1; j < N; j++){
        shI[j] = out[j - N/2+1][0];
        shQ[j] = out[j - N/2+1][1];
    }
    for(int j = 0; j < N; j++){
        P[j] = 20*log10(sqrt(shI[j]*shI[j] + shQ[j]*shQ[j])/N);
    }
    float m = 0;
    float rez_f = 0;
    for(int j = fi1; j < fi2; j++){
        float cm = sqrt(shI[j]*shI[j] + shQ[j]*shQ[j]);
        if(cm > m){
            m = cm;
            rez_f = freqs[j];
        }
    }

    m = m / N;
    m = 20*log10(m);

    try{
	  string fname = "freqs" + filePrefix + ".bin";
          ofstream out(fname.c_str(), ios::out | ios::binary);
          if(!out) {
            cout << "Cannot open file.";
            return 1;
           }

          out.write((char *) freqs, N*4);
          out.write((char *) P, N*4);
          out.write((char *) in_real, N*4);
          out.write((char *) in_imag, N*4);

          out.close();
    } catch (const std::exception& e){
        fprintf(stderr,"wr error");
    }
    return m;
}


// main code
int main(int argc, char** argv)
{
	bool is_need_start = true;
	FILE *fcom;
	string endCommand;
	string restartCommand;
		
    uint64_t freq_rec_hz; // частота в Гц
    uint64_t freq_sig_hz;
    double desired_sample_rate_hz; // количество выборок в сек
    double sample_rate_hz;
    const uint32_t lna_gain_db = 16;  // усиление на ПЧ
    const uint32_t vga_gain_db = 16;  // усиление на видеочастоте
    uint8_t rf_gain_on_off;       // ВЧ усиление 1 - вкл / 0 - выкл +12 дБ
    float atten_db;	
    char* serial_number = new char[32];//   "0000000000000000088869dc3382831b";
	int write_on_off;
	int duration; // время записи в секундах (желательно, указывать кратно секунде)
	filePrefix;
	folder;
	////////////////////////////////////////////////////////////////////
	// чтение имени файла конфигурации из параметров командной строки //
	////////////////////////////////////////////////////////////////////
	std::string val;
	std::string s;
	string confFileName = "";
	bool isConfigFileExist = false;
	// обработка входных аргументов
	for(int i = 0; i < argc; i=i+1){
		s = argv[i];
		if (s == "-cnfg"){
			val = argv[i+1];
			confFileName = string(argv[i+1]);
			isConfigFileExist = true;
		}
	}
	////////////////////////////////////////////////////////////////////
	
	/////////////////////////////////////////
	// проверка наличия файла конфигурации //
	/////////////////////////////////////////
	if(not(isConfigFileExist)){
		int a;
		cout << "\n\nФАЙЛ КОНФИГУРАЦИИ "<< confFileName.c_str() << "НЕ УКАЗАН !!!\n";
		cout << "ПРИЁМНИК НЕ МОЖЕТ БЫТЬ ИСПОЛЬЗОВАН БЕЗ КОНФИГУРАЦИИ\n";
		cout << "чтобы указать файл конфигурации надо написать -cnfg <имя файла>\n";
		cin >> a;
		return EXIT_FAILURE;
	}
	/////////////////////////////////////////
	bool is_first_run = true;
	while(is_need_start){
		is_need_start = false;
		
		//////////////////////////////////////////////////////////////////////
		// чтение содержимого файла и изменение параметров работы приёмника //
		//////////////////////////////////////////////////////////////////////
		fstream confFile;
		confFile.open(confFileName.c_str(),ios::in);
		if (confFile.is_open()){   //checking whether the file is open
			cout << "ФАЙЛ КОНФИГУРАЦИИ " << confFileName.c_str() << " НАЙДЕН\n";
			cout << " содержимое файла\n";
			string tp;
			while(getline(confFile, tp)){ //read data from file object and put it into string.
				cout << "  " <<tp << "\n"; //print the data of the string
				if(tp.find("RECIEVER_FREQUENCY_HZ = ") != string::npos){
					int i = 24;
					//freq_rec_hz = std::stoi(tp.substr(i,tp.length()-i));
					freq_rec_hz = std::stoul(tp.substr(i,tp.length()-i));
				} else if(tp.find("SAMPLERATE_HZ = ") != string::npos){
					int i = 16;
					desired_sample_rate_hz = std::stod(tp.substr(i,tp.length()-i));
				} else if(tp.find("SIGNAL_FREQUENCY_HZ = ") != string::npos){
					int i = 22;
					freq_sig_hz = std::stoul(tp.substr(i,tp.length()-i));
				} else if(tp.find("RF_ON_OFF = ") != string::npos){
					int i = 12;
					rf_gain_on_off = std::stoi(tp.substr(i,tp.length()-i));
				} else if(tp.find("WRITE_ON_OFF = ") != string::npos){
					int i = 15;
					write_on_off = std::stoi(tp.substr(i,tp.length()-i));
				} else if(tp.find("SERIAL_NUMBER = ") != string::npos){
					int i = 16;
					strcpy(serial_number, tp.substr(i,tp.length()-i).c_str());
				} else if (tp.find("DURATION_S = ") != string::npos){
					int i = 13;
					duration = std::stoi(tp.substr(i,tp.length()-i));
				} else if (tp.find("ATTEN_LEVEL_DB = ") != string::npos){
					int i = 17;
					atten_db = std::stoul(tp.substr(i,tp.length()-i));
				} else if(tp.find("PREFIX = ") != string::npos){
					int i = 9;
					filePrefix = tp.substr(i,tp.length()-i);
					endCommand = "endCommand" + filePrefix + ".txt";
					restartCommand = "restartCommand" + filePrefix + ".txt";
					if(fcom = fopen(endCommand.c_str(),"r")){
						fclose(fcom);
						std::remove(endCommand.c_str());
					}
					if(fcom = fopen(restartCommand.c_str(),"r")){
						fclose(fcom);
						std::remove(restartCommand.c_str());
					}
				} else if(tp.find("FOLDER = ") != string::npos){
					int i = 9;
					folder = tp.substr(i,tp.length()-i);
				}
			}
			confFile.close(); //close the file object.
			cout << "\n ПРОЧИТАННЫЕ ПАРАМЕТРЫ\n";
			cout << "  " << "RECIEVER_FREQUENCY_HZ = " << freq_rec_hz << '\n';
			cout << "  " << "SAMPLERATE_HZ = " << desired_sample_rate_hz << '\n';
			cout << "  " << "SIGNAL_FREQUENCY_HZ = " << freq_sig_hz << '\n';
			cout << "  " << "RF_ON_OFF = " << int(rf_gain_on_off) << '\n';
			cout << "  " << "WRITE_ON_OFF = " << write_on_off << '\n';
			cout << "  " << "SERIAL_NUMBER = " << serial_number << '\n';
			cout << "  " << "ATTEN_LEVEL_DB = " << atten_db << '\n';
			cout << "  " << "PREFIX = " << filePrefix << '\n';
			cout << "  " << "DURATION_S = " << duration << '\n';
			cout << "  " << "FOLDER = " << folder << '\n';
			
			sample_rate_hz = calculateSampleRate(desired_sample_rate_hz);
			int blocks_per_second = sample_rate_hz/131072;
			blocks_val = duration * blocks_per_second;
			sname = folder + filePrefix + "start_time.txt";
			ename = folder + filePrefix + "end_time.txt";
			if (is_first_run){
				write_on_off = 0;
				is_first_run = false;
				cout << "\n ПЕРВЫЙ ЗАПУСК (ЗАПИСЬ В ФАЙЛ НЕ ВЕДЕТСЯ)\n";
			}
			if (write_on_off == 1){
				need_write = true;
			} else {
				need_write = false;
			}
			
		} else {
			int a;
			cout << "\n\nФАЙЛ КОНФИГУРАЦИИ "<< confFileName.c_str() << " НЕ НАЙДЕН !!!\n";
			cin >> a;
			return EXIT_FAILURE;
		}
		//////////////////////////////////////////////////////////////////////
		
        //////////////////////////////
        // инициализация приёмников //
        //////////////////////////////
        int result = hackrf_init();
        hackrf_device* reciever= NULL;
        result = set_open_device(serial_number, &reciever);
        if(result != 0){
            int a;
            cin >> a;
            return EXIT_FAILURE;
        }
        ///////////////////////////////

        ///////////////////////////////
        // конфигурирование приёмника//
        ///////////////////////////////

        result = set_params(reciever,
							freq_rec_hz,
							desired_sample_rate_hz,
							lna_gain_db,
							vga_gain_db,
							rf_gain_on_off);
        if(result != 0){
            int a;
            cin >> a;
            return EXIT_FAILURE;
        }

        //////////////
        signal(SIGINT, my_handler);
        
        //////////////////////////////////////
        // запуск потоковой передачи данных //
        //////////////////////////////////////
        result |= hackrf_start_rx(reciever, rx_callback, NULL);
        if (result != 0)
        {
            fprintf(stderr, "hackrf_start_rx() failed: (%d)\n", result);
            return EXIT_FAILURE;
        } else {
            fprintf(stderr, "*************************\n");
            fprintf(stderr, "*******НАЧАЛ РАБОТУ******\n");
            fprintf(stderr, "*************************\n");
        }

        while (hackrf_is_streaming(reciever) != 1){
            cout << "стрим не смог запуститься" << hackrf_is_streaming(reciever) << "\n";
        }

        uint8_t buf_copy[262144]; // буфер для хранения данных из потока функции rx_callback
		////////////////////////////////////////
		
		//////////////////////////////////////
		// расчёт промежуточного результата //
		//////////////////////////////////////
		
			// для расчёта времени проверки наличия файлов с командами
		auto mt2 = std::chrono::high_resolution_clock::now();
		auto m2 = mt2.time_since_epoch();
		long long int t2 = m2.count();
		
		auto mt3 = std::chrono::high_resolution_clock::now();
		auto m3 = mt3.time_since_epoch();
		long long int t3 = m3.count();
			///////////////////////////////////////////////////////////
			
        long long int check_restart_time = 500000000;
        while(hackrf_is_streaming(reciever) == 1 && (do_exit == false))
        {
			usleep(100000);
			for(int i = 0; i < 262144; i++){
				buf_copy[i] = buf[i];
			}
			// fft
			float df = float(freq_sig_hz) - float(freq_rec_hz);
			//fprintf(stderr, "%0.2f\n", df);
			float rez = task_fft(buf_copy, df, 100e3, sample_rate_hz, 32768/2);
			
			// определение максимума
			double I,Q,P,mP;
		    mP = 0;
		    for(int i = 0; i < 262144; i+=2){
	
		    	I = double((int8_t)buf_copy[i]);
		        Q = double((int8_t)buf_copy[i+1]);
				P = sqrt(pow(I,2) + pow(Q,2));
				if(P > mP){
					mP = P;
				}
		    }
			fprintf(stderr, "max_alg: %0.2f Db fft_alg: %0.2f Db         \r", 20*log10(mP), rez);
			
		    try{
		        auto mt1 = std::chrono::high_resolution_clock::now();
		        auto m1 = mt1.time_since_epoch();
		        long long int t1 = m1.count();
		        string p_name2 = "powerOneLine" + filePrefix + ".txt";
		        FILE *p2 = fopen(p_name2.c_str(),"w");
		        fprintf(p2,"%llu;%0.2f\n",t1,rez);
		        fclose(p2);
		    } catch (const std::exception& e){
		        fprintf(stderr,"wr error");
		    }
			
			
			/////////////////////////////////
			// проверка файлов c командами //
			/////////////////////////////////
			mt2 = std::chrono::high_resolution_clock::now();
			m2 = mt2.time_since_epoch();
			t2 = m2.count();
			if(t2 - t3 > check_restart_time){
				mt3 = std::chrono::high_resolution_clock::now();
				m3 = mt3.time_since_epoch();
				t3 = m3.count();
				// файл команды завершения работы
				if(fcom = fopen(endCommand.c_str(),"r")){
					do_exit = true;
					fclose(fcom);
					std::remove(endCommand.c_str());
				// файл команды перезапуска с новыми параметрами
				} else if(fcom = fopen(restartCommand.c_str(),"r")){
					do_exit = true;
					is_need_start = true;
					fclose(fcom);
					std::remove(restartCommand.c_str());
				}
			}
			///////////////////////////////
				
        }
        //////////////////////////////////////
        
        ////////////////////////////////////
        // завершение работы с приёмником //
        ////////////////////////////////////
        do_exit = true;
        result = hackrf_close(reciever);
        if(result != 0)
        {
            fprintf(stderr, "hackrf_close() failed: (%d)\n", result);
            int a;
            cin >> a;
            return EXIT_FAILURE;

        } else {
            fprintf(stderr, "работа с приёмником завершена\n");
        }
        hackrf_exit();
        /////////////////////////////////////
		
		///////////////////////////////////////////////////////
		// возобновление цикла работы либо завершение работы //
		///////////////////////////////////////////////////////
        if(do_exit){
			if(isTerminateSignal){
				return 0;
			}
			if(!is_need_start){
				return 0;
			} else {
				sleep(1);
				do_exit = false;
			}
		}
		///////////////////////////////////////////////////////
		
	}
        
    
     return 0;

}
///////////////

