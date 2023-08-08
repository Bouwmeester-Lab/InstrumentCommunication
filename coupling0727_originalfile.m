function agilent_osc_communication()
%% initialize oscilloscope
%visaObj = visa('agilent','USB0::0x0957::0x179A::MY51450715::0::INSTR')
%visaObj = visa('agilent','USB0::2391::6042::MY52491664::0::INSTR')
%visaObj = visa('agilent','USB0::2391::6042::MY53160362::0::INSTR')
visaObj = visa('agilent','USB0::0x0957::0x179A::MY51250106::0::INSTR')
%% if doesn't work
a=instrfind
%%
visaObj =a(3)
%%
fclose(visaObj)
%% next step
% Set the buffer size
visaObj.InputBufferSize = 100000;
% Set the timeout value
visaObj.Timeout = 10;
% Set the Byte order
visaObj.ByteOrder = 'littleEndian';
% Open the connection
fopen(visaObj);
'opened'

 %% initialization for the measuremnt script
small_inno_V=[];
dip_detector_zero_V=[];
dip_V=zeros(10^6,2);
dip_Vi=1;
top_V=zeros(10^6,2);
top_Vi=1;
power_V=zeros(10^6,2);
power_Vi=1;
Temp_V=zeros(10^5,2);
Temp_Vi=1;
AMPL=zeros(10^5,21);
AMPLi=1;
index_top_V_start=1;
index_dip_V_start=1;
index_small_inno_V_start=1;
%writematrix([now 0], 'min_max.txt');
%%
% aux_n=4;
% V=2.2;
csvwrite('min_max0726.csv', [now 0])
csvwrite('topdipV0726.csv', [now 0 0])
%%
filename1 = 'min_max0727.csv';
filename2 = 'topdipV0727.csv.csv';
csvwrite('min_max0727.csv', [0 0])
%csvwrite('topdipV0727.csv', [0 0 0])
%%
time_pulse_tube_on=datenum('28-10-2020 16:00:00', 'dd-mm-yyyy HH:MM:SS')
time_pulse_tube_on=datenum('04-11-2020 16:00:00', 'dd-mm-yyyy HH:MM:SS')
time_pulse_tube_on=datenum('20-11-2020 13:00:00', 'dd-mm-yyyy HH:MM:SS')
time_pulse_tube_on=datenum('20-01-2023 11:15:00', 'dd-mm-yyyy HH:MM:SS') %Code failed because of polarization, restarted at that time, T=104K
time_pulse_tube_on=datenum('27-06-2023 12:27:00', 'dd-mm-yyyy HH:MM:SS')
time_pulse_tube_on=datenum('15-07-2023 12:27:00', 'dd-mm-yyyy HH:MM:SS')
%%
figure;plot(AMPL(1,2:end))
%%
Obj
%% initialize ZI 
Obj=zi_start_recording_demods(0.1, 'dev812', 1, 'y'); % zurich instrumentation communcation
Obj
zi_stop_recording_demods(Obj);
disp('done')
%% update curve //to read channel 1 and plot
h=figure;
upper_lim=1.2;
%ylim([-0.1 upper_lim])
%ylim([1.5 2])
while ishghandle(h)   
    X=scope_read_waveform(visaObj, 1);
    plot(X(:,1), X(:,2),'k')
    %mean(X(:,2))
    %min(X(:,2))
    ylim([-0.05 upper_lim])
    %ylim([1.5 2])
    pause(0.01)
end
%-0.0193 with no light
%% measurement script // while cryostat temperature changes
h=figure;hold on
ylim([-0.05 1.2])
i=0;
T_ampl=0.6;
V_dist=0;
V=zi_get_aux_offset(2);
dV=0.009;
r_min=0.8; % reflection threshold after which you consider you see a resonance
AMPLi=1;
%r_min=0.6;
prev_V_dist_sign=1;
aux_n=2; %temperature control of small innolight

%filename = 'topdipV0727.csv';
%T = table;
%TIME_LIST = [];
%DATA_LIST = [];

%filename = 'min_max0727.csv';
%T = table;
%TIME_LIST = [];
%DATA_LIST = [];
while ishghandle(h)    
    disp(i)
    %try
        X=scope_read_waveform(visaObj, 1); %cavity reflection from the oscilloscope
        h1=plot(X(:,2),'k');
        [a ind]=min(X(:,2)); % get the minima and the index for the reflection
        L=length(X(:,2));
        %[a ind/L]

        if ind>L/2
            top_V_cur=mean(X(1:(ind-round(L/10)),2)); % top_V_cur off resonance voltage
        else
            top_V_cur=mean(X((ind+round(L/10)):end,2)); % same but other side
        end

        if top_V_cur > 0.01 % && a/top_V_cur<0.9 % checks if you see any light       
            change=0;                
            if (max(X(:,2))-a)/max(X(:,2)) < r_min % coupling efficiency compared to threshold
                disp('search')
                %no dip, change V            
                % the one below changes the direction of the search on each iteration
                prev_V_dist_sign=-prev_V_dist_sign; % searches for the resonance by changing the voltage on the small inolight temperature control. Here we set the direction of the voltage change.

                V_dist = V_dist + dV % dv is the voltage step and vdist is the step we do on each iteration which increases by dV every new iteration
                %V=zi_get_aux_offset(4);
                V=V+V_dist*prev_V_dist_sign
                change=1; % this is the flag for telling the code to change the voltage on the zurich
            else
                disp('found')
                dip_V(dip_Vi, :)=[now a]; % saves the dip in an array with a timestamp
                dip_Vi=dip_Vi+1;
                top_V(top_Vi,:)=[now top_V_cur]; % saves the off resonance voltage
                top_Vi=top_Vi+1;
                i=i+1;
                
               % TIME_LIST1 = [TIME_LIST1,string(datetime('now'))];
                %DATA_LIST1(end+1) = top_V_cur;
                
                %T1.datetime = TIME_LIST1';
                %T1.data = DATA_LIST1';

                %writetable(T1,filename2)
                
                %V_data=csvread('topdipV0727.csv');
                %V_data=[V_data ; string(datetime('now')) top_V_cur a];
                %csvwrite('topdipV0727.csv', V_data);
                
                V_dist=0; % resets the search parameter for the search since you've found the resonance

                % bring to center by checking on which quadrant the peak is at, and if it's on the first it will change the voltage on the zurich by 0.002, if it's on the third by -0.002
                % these values are measured to work pretty realibly
                if ind < L/4
                    V = zi_get_aux_offset(2); % get the current auxiliary offset voltage
                    V = V+0.002;
                    change = 1;
                end
                if ind > 3*L/4
                    V = zi_get_aux_offset(2);
                    V = V-0.002;
                    change = 1;
                end  
            end

            if change % executes the change in the auxialiry output of the zurich
                small_inno_V=[small_inno_V; now V];
                disp(['------------------------------------------------------------new V ' num2str(V) ' ' datestr(now)])
                %small innolight: % checks if its in a mode hope free region
                if V<1.4
                    %V=V+(5.8-1.4-T_ampl); %mode hop free range
                    V=V+3.8; %mode hop free range
                end
                if V>5.4
                    V=V-3.8;
                end

                %big innolight
%                 if V<0.4                    
%                     V=V+2.5; %mode hop free range
%                 end
%                 if V>3.1
%                     V=V-2.5;
%                 end
                zi_set_aux_offset(aux_n, V) % sets the voltage

                if V_dist==0 % pause some time for things to thermalize, 1 sec if just centering or 5 seconds if searching for a peak
                    pause(1)
                else
                    pause(5)
                end
            end
        else
            % if no light log that we have no light at the time now
            dip_detector_zero_V=[dip_detector_zero_V; now top_V_cur];
        end

        %swap T
        swap_sign=1;
        if V > 5.3-0.6 % voltage sweep by 0.6V
        %if V>3.1-0.6
            swap_sign=-1;
        end
        
if mod(i, 5) == 1 && V > 1.5 && V < 5.3       %small innolight
        %if mod(i, 500)==1 && V>0.4 && V<3.1       %big
            disp('sweep') % sweeps the voltage by 0.6 V
            V_last=V;
            AMPL(AMPLi, 1)=now;
            for j=1:20 % steps in the sweep

                V=zi_get_aux_offset(2);
                V=V+swap_sign*T_ampl/25;
                zi_set_aux_offset(2, V)

                X=scope_read_waveform(visaObj, 1);
                %h1=plot(X(:,2),'k');
                [a ind]=min(X(:,2));
                L=length(X(:,2));
                %[a ind/L]            

                if ind>L/2
                    top_V_cur=mean(X(1:(ind-round(L/10)),2));        
                else
                    top_V_cur=mean(X((ind+round(L/10)):end,2));
                end
                AMPL(AMPLi, j+1)=top_V_cur;  
                pause(0.1)
            end
            
            AMPLi=AMPLi+1;
            Ratio_tip_interf=(max(AMPL(AMPLi-1, 2:end))-min(AMPL(AMPLi-1, 2:end)))/max(AMPL(AMPLi-1, 2:end));         % ignore the first element because it's the timestamp
            min_max=min(AMPL(AMPLi-1, 2:end))/max(AMPL(AMPLi-1, 2:end)) % same comment
            
            %TIME_LIST = [TIME_LIST,string(datetime('now'))];
            %DATA_LIST(end+1) = [min_max];
                        
            %T.datetime = TIME_LIST'
            %T.data = DATA_LIST'

            %writetable(T,filename)
            min_max_curr=csvread('min_max0727.csv');
            min_max_curr=[min_max_curr ; 'now' min_max];
            csvwrite('min_max0727.csv', min_max_curr)
           
            ok=0;
            while abs(zi_get_aux_offset(2)-V_last)>0.1
                'get_back'
                V_last
                zi_set_aux_offset(2, V_last)
                pause(0.2)
            end
            i=i+1;
            V=V_last;
            pause(10)
end
            
        pause(0.1)
        delete(h1)
end % end of sweep and track of the peak, only this will be ported to python
%% csvwrite
h=figure;hold on
ylim([-0.05 0.5])
i=0;
T_ampl=0.6;
V_dist=0;
V=zi_get_aux_offset(2);
dV=0.009;
r_min=0.8;
AMPLi=1;
%r_min=0.6;
prev_V_dist_sign=1;
aux_n=2; %temperature control of small innolight
csvwrite('min_max0727.csv', [0 0 0])
while ishghandle(h)    
    %try
        X=scope_read_waveform(visaObj, 1); %cavity reflection
        h1=plot(X(:,2),'k');
        [a ind]=min(X(:,2));
        L=length(X(:,2));
        %[a ind/L]

        i=i+1;
        pause(1)
         
        if mod(i, 3)==1 && V>1.5 && V<5.3       %small innolight
        %if mod(i, 500)==1 && V>0.4 && V<3.1       %big
            disp('sweep')
            V_last=V;
            AMPL(AMPLi, 1)=now;
            for j=1:5

                V=zi_get_aux_offset(2);
                V=V+swap_sign*T_ampl/25;
                zi_set_aux_offset(2, V)

                X=scope_read_waveform(visaObj, 1);
                %h1=plot(X(:,2),'k');
                [a ind]=min(X(:,2));
                L=length(X(:,2));
                %[a ind/L]            

                if ind>L/2
                    top_V_cur=mean(X(1:(ind-round(L/10)),2));        
                else
                    top_V_cur=mean(X((ind+round(L/10)):end,2));
                end
                AMPL(AMPLi, j+1)=top_V_cur;  
                pause(0.1)
            end
            %previous run
            %Ratio_tip_interf=(max(AMPL(AMPLi-1, 2:end))-min(AMPL(AMPLi-1, 2:end)))/max(AMPL(AMPLi-1, 2:end))
            %AMPLi=AMPLi+1;
            AMPLi=AMPLi+1;
            Ratio_tip_interf=(max(AMPL(AMPLi-1, 2:end))-min(AMPL(AMPLi-1, 2:end)))/max(AMPL(AMPLi-1, 2:end));            
            min_max=min(AMPL(AMPLi-1, 2:end))+0.00375/max(AMPL(AMPLi-1, 2:end))+0.00375

            min_max_curr=csvread('min_max0727.csv');
            a=string(datetime('now'))
            newStr = extractAfter(a,"2023 ")
            T = extractBetween(a,13,14)
            TT = extractBetween(a,16,17)
            min_max_curr=[min_max_curr; T TT min_max];
            csvwrite('min_max0727.csv', min_max_curr)
            
            ok=0;
            while abs(zi_get_aux_offset(2)-V_last)>0.1
                'get_back'
                V_last
                zi_set_aux_offset(2, V_last)
                pause(0.2)
            end
            V=V_last;
            zi_set_aux_offset(2, V);
            pause(10)
        end
        
        %writetable(T,filename)
        %read power occasionally
        if mod(i,10)==1        
            try
                delete(h2)
            catch
            end
            last_power=scope_read_waveform(visaObj, 2);        
            h2=plot(last_power(:,2)/2,'b');
            power_V(power_Vi, :)=[now mean(last_power(:,2))];
            power_Vi=power_Vi+1;
        end
        pause(0.1)
        delete(h1)

end
%% 
if mod(i, 3)==1 && V>1.5 && V<5.3       %small innolight
        %if mod(i, 500)==1 && V>0.4 && V<3.1       %big
            disp('sweep')
            V_last=V;
            AMPL(AMPLi, 1)=now;
            for j=1:20

                V=zi_get_aux_offset(2);
                V=V+swap_sign*T_ampl/25;
                zi_set_aux_offset(2, V)

                X=scope_read_waveform(visaObj, 1);
                %h1=plot(X(:,2),'k');
                [a ind]=min(X(:,2));
                L=length(X(:,2));
                %[a ind/L]            

                if ind>L/2
                    top_V_cur=mean(X(1:(ind-round(L/10)),2));        
                else
                    top_V_cur=mean(X((ind+round(L/10)):end,2));
                end
                AMPL(AMPLi, j+1)=top_V_cur;  
                pause(0.1)
            end
            %previous run
            %Ratio_tip_interf=(max(AMPL(AMPLi-1, 2:end))-min(AMPL(AMPLi-1, 2:end)))/max(AMPL(AMPLi-1, 2:end))
            %AMPLi=AMPLi+1;
            AMPLi=AMPLi+1;
            Ratio_tip_interf=(max(AMPL(AMPLi-1, 2:end))-min(AMPL(AMPLi-1, 2:end)))/max(AMPL(AMPLi-1, 2:end));            
            min_max=min(AMPL(AMPLi-1, 2:end))+0.00375/max(AMPL(AMPLi-1, 2:end))+0.00375
 
            ok=0;
            while abs(zi_get_aux_offset(2)-V_last)>0.1
                'get_back'
                V_last
                zi_set_aux_offset(2, V_last)
                pause(0.2)
            end
            V=V_last;
            zi_set_aux_offset(2, V);
            pause(10)
        end
%%
V=zi_get_aux_offset(2)
if  V>1.5 && V<5.3       %small innolight
        %if mod(i, 500)==1 && V>0.4 && V<3.1       %big
            disp('sweep')
            V_last=V;
            AMPL(AMPLi, 1)=now;
            for j=1:20

                V=zi_get_aux_offset(2);
                V=V+swap_sign*T_ampl/25;
                zi_set_aux_offset(2, V)

                X=scope_read_waveform(visaObj, 1);
                %h1=plot(X(:,2),'k');
                [a ind]=min(X(:,2));
                L=length(X(:,2));
                %[a ind/L]            

                if ind>L/2
                    top_V_cur=mean(X(1:(ind-round(L/10)),2));        
                else
                    top_V_cur=mean(X((ind+round(L/10)):end,2));
                end
                AMPL(AMPLi, j+1)=top_V_cur;  
                pause(0.1)
            end
            
            AMPLi=AMPLi+1;
            Ratio_tip_interf=(max(AMPL(AMPLi-1, 2:end))-min(AMPL(AMPLi-1, 2:end)))/max(AMPL(AMPLi-1, 2:end));            
            min_max=min(AMPL(AMPLi-1, 2:end))/max(AMPL(AMPLi-1, 2:end))
           
            while abs(zi_get_aux_offset(2)-V_last)>0.1
                'get_back'
                V_last
                zi_set_aux_offset(2, V_last)
                pause(0.2)
            end
            i=i+1;
            V=V_last;
            pause(10)
end
%% 
clc

%????
filename  = '0801_2.csv';
V=zi_get_aux_offset(2);
AMPLi=1;
cycle = 10;

%if ~exist(filename) %????????
 %   csvwrite(filename, [])
%end

T = table;
TIME_LIST = [];
DATA_LIST = [];



for n = 1:cycle
    TIME_LIST = [TIME_LIST,string(datetime('now'))];  
   
     V=zi_get_aux_offset(2);
     if  V>1.5 && V<5.3       %small innolight
        %if mod(i, 500)==1 && V>0.4 && V<3.1       %big
            disp('sweep')
            V_last=V;
            AMPL(AMPLi, 1)=now;
            for j=1:20

                V=zi_get_aux_offset(2);
                V=V+swap_sign*T_ampl/25;
                zi_set_aux_offset(2, V)

                X=scope_read_waveform(visaObj, 1);
                %h1=plot(X(:,2),'k');
                [a ind]=min(X(:,2));
                L=length(X(:,2));
                %[a ind/L]            

                if ind>L/2
                    top_V_cur=mean(X(1:(ind-round(L/10)),2));        
                else
                    top_V_cur=mean(X((ind+round(L/10)):end,2));
                end
                AMPL(AMPLi, j+1)=top_V_cur;  
                pause(0.1)
            end
            
            AMPLi=AMPLi+1;
            Ratio_tip_interf=(max(AMPL(AMPLi-1, 2:end))-min(AMPL(AMPLi-1, 2:end)))/max(AMPL(AMPLi-1, 2:end));            
            min_max=min(AMPL(AMPLi-1, 2:end))/max(AMPL(AMPLi-1, 2:end))
           
            while abs(zi_get_aux_offset(2)-V_last)>0.1
                'get_back'
                V_last
                zi_set_aux_offset(2, V_last)
                pause(0.2)
            end
            i=i+1;
            V=V_last;
            pause(300)
    end
    
    DATA_LIST(end+1) = min_max;
    %pause(30)
end

T.datetime = TIME_LIST'
T.data = DATA_LIST'

writetable(T,filename)
%% 
fclose('all')
%% Only Fiber tip table
h=figure;hold on
ylim([-0.05 0.5])
i=0;
T_ampl=0.6;
V_dist=0;
V=zi_get_aux_offset(2);
dV=0.009;
r_min=0.8;
AMPLi=1;
%r_min=0.6;
prev_V_dist_sign=1;
aux_n=2; %temperature control of small innolight
csvwrite('min_max0727.csv', [0 0])
filename  = 'test.csv';
while ishghandle(h)    
    %try
        X=scope_read_waveform(visaObj, 1); %cavity reflection
        h1=plot(X(:,2),'k');
        [a ind]=min(X(:,2));
        L=length(X(:,2));
        %[a ind/L]

        i=i+1;
        pause(1)
         
        if mod(i, 3)==1 && V>1.5 && V<5.3       %small innolight
        %if mod(i, 500)==1 && V>0.4 && V<3.1       %big
            disp('sweep')
            V_last=V;
            AMPL(AMPLi, 1)=now;
            for j=1:5

                V=zi_get_aux_offset(2);
                V=V+swap_sign*T_ampl/25;
                zi_set_aux_offset(2, V)

                X=scope_read_waveform(visaObj, 1);
                %h1=plot(X(:,2),'k');
                [a ind]=min(X(:,2));
                L=length(X(:,2));
                %[a ind/L]            

                if ind>L/2
                    top_V_cur=mean(X(1:(ind-round(L/10)),2));        
                else
                    top_V_cur=mean(X((ind+round(L/10)):end,2));
                end
                AMPL(AMPLi, j+1)=top_V_cur;  
                pause(0.1)
            end
            %previous run
            %Ratio_tip_interf=(max(AMPL(AMPLi-1, 2:end))-min(AMPL(AMPLi-1, 2:end)))/max(AMPL(AMPLi-1, 2:end))
            %AMPLi=AMPLi+1;
            AMPLi=AMPLi+1;
            Ratio_tip_interf=(max(AMPL(AMPLi-1, 2:end))-min(AMPL(AMPLi-1, 2:end)))/max(AMPL(AMPLi-1, 2:end));            
            min_max=min(AMPL(AMPLi-1, 2:end))+0.00375/max(AMPL(AMPLi-1, 2:end))+0.00375
            
            T = table;
            TIME_LIST = [];
            DATA_LIST = [];

            TIME_LIST = [TIME_LIST,string(datetime('now'))];
            DATA_LIST = min_max;
                        
            T.datetime = TIME_LIST'
            T.data = DATA_LIST'  
            writetable(T,filename)
         
            ok=0;
            while abs(zi_get_aux_offset(2)-V_last)>0.1
                'get_back'
                V_last
                zi_set_aux_offset(2, V_last)
                pause(0.2)
            end
            V=V_last;
            zi_set_aux_offset(2, V);
            pause(10)
        end
        
       
        fclose('all')
        %read power occasionally
        if mod(i,10)==1        
            try
                delete(h2)
            catch
            end
            last_power=scope_read_waveform(visaObj, 2);        
            h2=plot(last_power(:,2)/2,'b');
            power_V(power_Vi, :)=[now mean(last_power(:,2))];
            power_Vi=power_Vi+1;
        end
        pause(0.1)
        delete(h1)

end
%%
i=1;
figure;plot(AMPL(i,2:21))
%%
time_pulse_tube_on=now;
%%
time_pulse_tube_on=datenum('17.01.2023 12:18:00', 'dd.mm.yyyy HH:MM:SS')
%%
hour_start=0;
index_top_V_start=sum((top_V(1:top_Vi-1,1)-time0)*24<hour_start)
index_dip_V_start=sum((dip_V(1:dip_Vi-1,1)-time0)*24<hour_start)
index_small_inno_V_start=sum((small_inno_V(:,1)-time0)*24<hour_start)
index_power_start=sum((power_V(1:power_Vi-1,1)-time0)*24<hour_start)
index_start=1;
%%
time0=floor(dip_V(1,1));
time0=time_pulse_tube_on;
figure;plot((dip_V(index_dip_V_start:dip_Vi-1,1)-time0)*24, dip_V(index_dip_V_start:dip_Vi-1,2)+0.019)
hold on;
plot((top_V(index_top_V_start:top_Vi-1,1)-time0)*24, top_V(index_top_V_start:top_Vi-1,2))
plot((power_V(index_power_start:power_Vi-1,1)-time0)*24, 1.1/0.62*13/30*power_V(index_power_start:power_Vi-1,2))
%figure;
plot((small_inno_V(index_small_inno_V_start:end,1)-time0)*24, small_inno_V(index_small_inno_V_start:end,2)/2.5,'m')
xlabel('Time, h')
ylim([0 2.5])
%
Y=[];
MIN_MAX=[];
for i=1:AMPLi-1    
    Y=[Y; AMPL(i,1) min(AMPL(i,2:21))/max(AMPL(i,2:21))];
    MIN_MAX=[MIN_MAX; Y(i,1) min(AMPL(i,2:21)) max(AMPL(i,2:21))];
end
% figure;hold on
% plot((MIN_MAX(index_start:end,1)-time0)*24, MIN_MAX(index_start:end,2))
% plot((MIN_MAX(index_start:end,1)-time0)*24, MIN_MAX(index_start:end,3))
% plot((power_V(index_power_start:power_Vi-1,1)-time0)*24, 1.15*1.1/0.62*13/30*power_V(index_power_start:power_Vi-1,2))

%figure;plot((MIN_MAX(:,1)-time0)*24, MIN_MAX(:,2)./MIN_MAX(:,3))

for i=1:length(Y)
    MIN_MAX(i,4)=tip_mirror_coupling(MIN_MAX(i,2)/MIN_MAX(i,3)/(1-0.0025*8));
end
%figure;plot((Y(:,1)-floor(dip_V(1,1)))*24, Y(:,2))
figure;plot((MIN_MAX(index_start:end,1)-time0)*24, MIN_MAX(index_start:end,4));ylabel('tip-1st mirror coupling');xlabel('Time, h')
figure;plot((MIN_MAX(index_start:end,1)-time0)*24, MIN_MAX(index_start:end,2)./MIN_MAX(index_start:end,3));ylabel('min(R)/max(R)')


xlabel('Time, h')
%ylim([0.6 1])
%%
figure;plot(MIN_MAX(:,1), MIN_MAX(:,2))
hold on;plot(MIN_MAX(:,1), MIN_MAX(:,3))
%%
MIN=[MIN_MAX(:,1) MIN_MAX(:,2)];
MAX=[MIN_MAX(:,1) MIN_MAX(:,3)];
%%
figure;plot((power_V(1:power_Vi-1,1)-time0)*24, 13/30*power_V(1:power_Vi-1,2))
%POW=[(power_V(1:power_Vi-1,1)-time0)*24 power_V(1:power_Vi-1,2)];
POW=[(power_V(1:power_Vi-1,1))*24 power_V(1:power_Vi-1,2)];
%% power corrected
MIN_power=log_T_time2T(MIN, POW,100);
figure;plot(MIN(:,1), MIN(:,2)./MIN_power)
%% power corrected
MAX_power=log_T_time2T(MAX, POW,100);
hold on;plot(MAX(:,1), MAX(:,2)./MAX_power)
%%
MAX_power=log_T_time2T(MAX, POW,100);
%% sweep small laser T and measure reflection
T_ampl=8;
V=zi_get_aux_offset(2);
V_last=V;
AMPLi=1;
for j=1:1000

    V=zi_get_aux_offset(2);
    V=V+T_ampl/1000;
    zi_set_aux_offset(2, V)

    X=scope_read_waveform(visaObj, 1);
    %h1=plot(X(:,2),'k');
    [a ind]=min(X(:,2));
    L=length(X(:,2));
    %[a ind/L]            

    if ind>L/2
        top_V_cur=mean(X(1:(ind-round(L/10)),2));        
    else
        top_V_cur=mean(X((ind+round(L/10)):end,2));
    end
    AMPL(AMPLi, j+1)=top_V_cur;  
    Volt(j)=V;
    pause(0.1)
end
%previous run
%Ratio_tip_interf=(max(AMPL(AMPLi-1, 2:end))-min(AMPL(AMPLi-1, 2:end)))/max(AMPL(AMPLi-1, 2:end))
%AMPLi=AMPLi+1;
AMPLi=AMPLi+1;
Ratio_tip_interf=(max(AMPL(AMPLi-1, 2:end))-min(AMPL(AMPLi-1, 2:end)))/max(AMPL(AMPLi-1, 2:end))            
ok=0;
while abs(zi_get_aux_offset(2)-V_last)>0.1
    'get_back'
    V_last
    zi_set_aux_offset(2, V_last)
    pause(0.2)
end
i=i+1;
V=V_last;


%%
i=1;
figure;plot(AMPL(AMPLi-1,2:end))
%figure;plot(Volt, AMPL(AMPLi-1,2:end))

%%
figure;plot((dip_V(1:dip_Vi-1,1)-floor(dip_V(1,1)))*24, 1-(0.019+dip_V(1:dip_Vi-1,2))./top_V(1:top_Vi-1,2))
%%
xlabel('Time, h')
ylabel('Reflection signal, V')
%%
% Example to connect to and download waveform data from an oscilloscope
% This example connects to an Agilent scope using VISA and sends SCPI
% commands to initiate acquisition and downloads the data and displays it 
% in MATLAB
% 
% Note that this demo requires you to have Agilent IO Libraries installed.
% The VISA resource string to the oscilloscope is to be obtained from
% Agilent connection expert.
% 
% Copyright 2010 The MathWorks, Inc
%% Interface configuration and instrument connection
% The second argument to the VISA function is the resource string for your
% instrument
%visaObj = visa('agilent','TCPIP0::172.31.57.44::inst0::INSTR');
%visaObj = visa('agilent','USB0::2391::6042::MY51450715::0::INSTR');
a=instrfind
%%
visaObj = visa('agilent','USB0::0x0957::0x179A::MY51450715::0::INSTR')
%%
visaObj =a(1)
%%
% Set the buffer size
visaObj.InputBufferSize = 100000;
% Set the timeout value
visaObj.Timeout = 10;
% Set the Byte order
visaObj.ByteOrder = 'littleEndian';
% Open the connection
fopen(visaObj);
'opened'
% Instrument control and data retreival
% Now control the instrument using SCPI commands. refer to the instrument
% programming manual for your instrument for the correct SCPI commands for
% your instrument.
% Reset the instrument and autoscale and stop
%%
visaObj = visa('agilent','USB0::0x0957::0x179A::MY51450715::0::INSTR')
%%
fopen(visaObj);
%%
fclose(visaObj);
%%
%%

a=instrfind
%%
visaObj=a(3)
%%
'read'
waveform.RawData = binblockread(visaObj,'uint16'); fread(visaObj,1);
'done'
%%
visaObj.InputBufferSize = 100000;
% Set the timeout value
visaObj.Timeout = 10;
% Set the Byte order
visaObj.ByteOrder = 'littleEndian';

fopen(visaObj);
'opened'
%%
figure;


%% single curve
figure
ylim([0 2])
X=scope_read_waveform(visaObj, 1);
plot(X(:,1), X(:,2),'k')

%% POWER curve
X=scope_read_waveform(visaObj, 2);
plot(X(:,1), X(:,2))

%% search
%find refl dip, assume dip is more than 20%
h=figure;hold on
ylim([0 2])
i=1;
dV=0.002;
V_dist=0;
prev_V_dist_sign=-1;
V=zi_get_aux_offset(4);
while ishghandle(h)    
    X=scope_read_waveform(visaObj, 1);
    h1=plot(X(:,2),'k');
    [a ind]=min(X(:,2));
    L=length(X(:,2));
    %[a ind/L]
    % go up
    r_min=0.2;    

        if ind>L/2
            top_V_cur=mean(X(1:(ind-round(L/10)),2));        
        else
            top_V_cur=mean(X((ind+round(L/10)):end,2));
        end

    
    if top_V_cur>0.1% && a/top_V_cur<0.9
        change=0;
        if (max(X(:,2))-a)/max(X(:,2))<r_min
            %no dip, change V            
            prev_V_dist_sign=-prev_V_dist_sign;
            V_dist=V_dist+dV
            %V=zi_get_aux_offset(4);
            V=V+V_dist*prev_V_dist_sign
            change=1;
        else
            'found'
            V_dist=0;
        end
  
        if change
            %small_inno_V=[small_inno_V; now V];
            disp(['------------------------------------------------------------new V ' num2str(V) ' ' datestr(now)])
            if V<1 || V>3
                asd
            end
            zi_set_aux_offset(aux_n, V)

            pause(3)
        end
    else
        %no light
        dip_detector_zero_V=[dip_detector_zero_V; now top_V_cur];
    end
    %read power occasionally
%     if mod(i,10)==1        
%         try
%             delete(h2)
%         catch
%         end
%         last_power=scope_read_waveform(visaObj, 2);        
%         h2=plot(last_power(:,2)*10,'b');
%         power_V(power_Vi, :)=[now mean(last_power(:,2))];
%         power_Vi=power_Vi+1;
%     end
    pause(0.1)
    delete(h1)
    i=i+1;
end


%%
AMPL=zeros(10^5,20);
AMPLi=1;

%%

figure;hold on
for i=1:10
    plot(rand(2,1))
    pause(0.5)
end
%%
[a ind]=min(X(:,2))
%%
X=zeros(100,1);
for i=1:10
    %fprintf(visaObj,'*RST; :AUTOSCALE'); 
    %fprintf(visaObj,':STOP');
    fprintf(visaObj,':SINGLE');
    % Specify data from Channel 1
    fprintf(visaObj,':WAVEFORM:SOURCE CHAN1'); 
    % Set timebase to main
    fprintf(visaObj,':TIMEBASE:MODE MAIN');
    % Set up acquisition type and count. 
    fprintf(visaObj,':ACQUIRE:TYPE NORMAL');
    fprintf(visaObj,':ACQUIRE:COUNT 1');
    % Specify 5000 points at a time by :WAV:DATA?
    fprintf(visaObj,':WAV:POINTS:MODE RAW');
    fprintf(visaObj,':WAV:POINTS 5000');
    % Now tell the instrument to digitize channel1
    fprintf(visaObj,':DIGITIZE CHAN1');
    % Wait till complete
    operationComplete = str2double(query(visaObj,'*OPC?'))
    while ~operationComplete
        operationComplete = str2double(query(visaObj,'*OPC?'))
    end
    % Get the data back as a WORD (i.e., INT16), other options are ASCII and BYTE
    fprintf(visaObj,':WAVEFORM:FORMAT WORD');
    % Set the byte order on the instrument as well
    fprintf(visaObj,':WAVEFORM:BYTEORDER LSBFirst');
    % Get the preamble block
    preambleBlock = query(visaObj,':WAVEFORM:PREAMBLE?');
    % The preamble block contains all of the current WAVEFORM settings.  
    % It is returned in the form <preamble_block><NL> where <preamble_block> is:
    %    FORMAT        : int16 - 0 = BYTE, 1 = WORD, 2 = ASCII.
    %    TYPE          : int16 - 0 = NORMAL, 1 = PEAK DETECT, 2 = AVERAGE
    %    POINTS        : int32 - number of data points transferred.
    %    COUNT         : int32 - 1 and is always 1.
    %    XINCREMENT    : float64 - time difference between data points.
    %    XORIGIN       : float64 - always the first data point in memory.
    %    XREFERENCE    : int32 - specifies the data point associated with
    %                            x-origin.
    %    YINCREMENT    : float32 - voltage diff between data points.
    %    YORIGIN       : float32 - value is the voltage at center screen.
    %    YREFERENCE    : int32 - specifies the data point where y-origin
    %                            occurs.
    % Now send commmand to read data
    fprintf(visaObj,':WAV:DATA?');
    % read back the BINBLOCK with the data in specified format and store it in
    % the waveform structure. FREAD removes the extra terminator in the buffer
    'read'
    waveform.RawData = binblockread(visaObj,'uint16'); fread(visaObj,1);
    'done'
    %

    % Data processing: Post process the data retreived from the scope
    % Extract the X, Y data and plot it 
    % Maximum value storable in a INT16
    maxVal = 2^16; 
    %  split the preambleBlock into individual pieces of info
    preambleBlock = regexp(preambleBlock,',','split');
    % store all this information into a waveform structure for later use
    waveform.Format = str2double(preambleBlock{1});     % This should be 1, since we're specifying INT16 output
    waveform.Type = str2double(preambleBlock{2});
    waveform.Points = str2double(preambleBlock{3});
    waveform.Count = str2double(preambleBlock{4});      % This is always 1
    waveform.XIncrement = str2double(preambleBlock{5}); % in seconds
    waveform.XOrigin = str2double(preambleBlock{6});    % in seconds
    waveform.XReference = str2double(preambleBlock{7});
    waveform.YIncrement = str2double(preambleBlock{8}); % V
    waveform.YOrigin = str2double(preambleBlock{9});
    waveform.YReference = str2double(preambleBlock{10});
    waveform.VoltsPerDiv = (maxVal * waveform.YIncrement / 8);      % V
    waveform.Offset = ((maxVal/2 - waveform.YReference) * waveform.YIncrement + waveform.YOrigin);         % V
    waveform.SecPerDiv = waveform.Points * waveform.XIncrement/10 ; % seconds
    waveform.Delay = ((waveform.Points/2 - waveform.XReference) * waveform.XIncrement + waveform.XOrigin); % seconds
    % Generate X & Y Data
    waveform.XData = (waveform.XIncrement.*(1:length(waveform.RawData))) - waveform.XIncrement;
    waveform.YData = (waveform.YIncrement.*(waveform.RawData - waveform.YReference)) + waveform.YOrigin; 
    X(i)=min(waveform.YData);
    i
%     % Plot it
%     %figure
%     plot(waveform.XData,waveform.YData);
%     set(gca,'XTick',(min(waveform.XData):waveform.SecPerDiv:max(waveform.XData)))
%     xlabel('Time (s)');
%     ylabel('Volts (V)');
%     title('Oscilloscope Data');
%     grid on;
end
figure;plot(X)
%%
%fprintf(visaObj,'*RST; :AUTOSCALE'); 
%fprintf(visaObj,':STOP');
%fprintf(visaObj,':SINGLE');
% Specify data from Channel 1
fprintf(visaObj,':WAVEFORM:SOURCE CHAN3'); 
% Set timebase to main
fprintf(visaObj,':TIMEBASE:MODE MAIN');
% Set up acquisition type and count. 
fprintf(visaObj,':ACQUIRE:TYPE NORMAL');
fprintf(visaObj,':ACQUIRE:COUNT 1');
% Specify 5000 points at a time by :WAV:DATA?
fprintf(visaObj,':WAV:POINTS:MODE RAW');
fprintf(visaObj,':WAV:POINTS 5000');
% Now tell the instrument to digitize channel1
fprintf(visaObj,':DIGITIZE CHAN3');
% Wait till complete
operationComplete = str2double(query(visaObj,'*OPC?'))
while ~operationComplete
    operationComplete = str2double(query(visaObj,'*OPC?'))
end
% Get the data back as a WORD (i.e., INT16), other options are ASCII and BYTE
fprintf(visaObj,':WAVEFORM:FORMAT WORD');
% Set the byte order on the instrument as well
fprintf(visaObj,':WAVEFORM:BYTEORDER LSBFirst');
% Get the preamble block
preambleBlock = query(visaObj,':WAVEFORM:PREAMBLE?');
% The preamble block contains all of the current WAVEFORM settings.  
% It is returned in the form <preamble_block><NL> where <preamble_block> is:
%    FORMAT        : int16 - 0 = BYTE, 1 = WORD, 2 = ASCII.
%    TYPE          : int16 - 0 = NORMAL, 1 = PEAK DETECT, 2 = AVERAGE
%    POINTS        : int32 - number of data points transferred.
%    COUNT         : int32 - 1 and is always 1.
%    XINCREMENT    : float64 - time difference between data points.
%    XORIGIN       : float64 - always the first data point in memory.
%    XREFERENCE    : int32 - specifies the data point associated with
%                            x-origin.
%    YINCREMENT    : float32 - voltage diff between data points.
%    YORIGIN       : float32 - value is the voltage at center screen.
%    YREFERENCE    : int32 - specifies the data point where y-origin
%                            occurs.
% Now send commmand to read data
fprintf(visaObj,':WAV:DATA?');
% read back the BINBLOCK with the data in specified format and store it in
% the waveform structure. FREAD removes the extra terminator in the buffer
'read'
waveform.RawData = binblockread(visaObj,'uint16'); fread(visaObj,1);
'done'

% Data processing: Post process the data retreived from the scope
% Extract the X, Y data and plot it 
% Maximum value storable in a INT16
maxVal = 2^16; 
%  split the preambleBlock into individual pieces of info
preambleBlock = regexp(preambleBlock,',','split');
% store all this information into a waveform structure for later use
waveform.Format = str2double(preambleBlock{1});     % This should be 1, since we're specifying INT16 output
waveform.Type = str2double(preambleBlock{2});
waveform.Points = str2double(preambleBlock{3});
waveform.Count = str2double(preambleBlock{4});      % This is always 1
waveform.XIncrement = str2double(preambleBlock{5}); % in seconds
waveform.XOrigin = str2double(preambleBlock{6});    % in seconds
waveform.XReference = str2double(preambleBlock{7});
waveform.YIncrement = str2double(preambleBlock{8}); % V
waveform.YOrigin = str2double(preambleBlock{9});
waveform.YReference = str2double(preambleBlock{10});
waveform.VoltsPerDiv = (maxVal * waveform.YIncrement / 8);      % V
waveform.Offset = ((maxVal/2 - waveform.YReference) * waveform.YIncrement + waveform.YOrigin);         % V
waveform.SecPerDiv = waveform.Points * waveform.XIncrement/10 ; % seconds
waveform.Delay = ((waveform.Points/2 - waveform.XReference) * waveform.XIncrement + waveform.XOrigin); % seconds
% Generate X & Y Data
waveform.XData = (waveform.XIncrement.*(1:length(waveform.RawData))) - waveform.XIncrement;
waveform.YData = (waveform.YIncrement.*(waveform.RawData - waveform.YReference)) + waveform.YOrigin; 
% Plot it
hold on
plot(waveform.XData,waveform.YData/60);
set(gca,'XTick',(min(waveform.XData):waveform.SecPerDiv:max(waveform.XData)))
xlabel('Time (s)');
ylabel('Volts (V)');
title('Oscilloscope Data');
grid on;
%% Now let's also get the screenshot of the instrument and display it in MATLAB
% Grab the screen from the instrument and display it
% Set the buffer size to a large value sinze the BMP could be large
visaObj.InputBufferSize = 10000000;
% reopen the connection
fopen(visaObj);
% send command and get BMP.
fprintf(visaObj,':DISPLAY:DATA? BMP, SCREEN, GRAYSCALE');
screenBMP = binblockread(visaObj,'uint8'); fread(visaObj,1);
% save as a BMP  file
fid = fopen('test1.bmp','w');
fwrite(fid,screenBMP,'uint8');
fclose(fid);
% Read the BMP and display image
figure; colormap(gray(256)); 
imageMatrix = imread('test1.bmp','bmp');
image(imageMatrix); 
% Adjust the figure so it shows accurately
sizeImg = size(imageMatrix);
set(gca,'Position',[0 0 1 1],'XTick' ,[],'YTick',[]); set(gcf,'Position',[50 50 sizeImg(2) sizeImg(1)]);
axis off; axis image;
% Delete objects and clear them.
delete(visaObj); clear visaObj;
end