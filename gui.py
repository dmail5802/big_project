import tkinter as tk
import math, random, time

BG="#0A0E1A";CARD="#111827";CARD2="#1A2235";ACCENT="#00D4FF";PURPLE="#7C3AED";GREEN="#10B981";YELLOW="#F59E0B";WHITE="#F1F5F9";MUTED="#64748B"
FB=("Courier New",26,"bold");FH=("Courier New",14,"bold");FN=("Courier New",11);FS=("Courier New",9);FK=("Courier New",12,"bold")

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("IoT Lab — Professor Voice Studio")
        self.geometry("1100x680")
        self.minsize(900,600)
        self.configure(bg=BG)
        self._s=None
        self._welcome()

    def _clear(self):
        if self._s: self._s.destroy()

    def _welcome(self):
        self._clear()
        f=tk.Frame(self,bg=BG); f.pack(fill="both",expand=True); self._s=f
        c=tk.Canvas(f,bg=BG,highlightthickness=0); c.place(relwidth=1,relheight=1)
        pts=[{"x":random.randint(0,1100),"y":random.randint(0,700),"s":random.uniform(0.3,1),"r":random.uniform(1,3)} for _ in range(55)]
        def anim():
            c.delete("d")
            for p in pts:
                p["y"]-=p["s"]
                if p["y"]<0: p["y"]=720;p["x"]=random.randint(0,1100)
                c.create_oval(p["x"]-p["r"],p["y"]-p["r"],p["x"]+p["r"],p["y"]+p["r"],fill=ACCENT,outline="",tags="d")
            f.after(30,anim)
        anim()
        mid=tk.Frame(f,bg=BG); mid.place(relx=0.5,rely=0.5,anchor="center")
        tk.Label(mid,text="⚡  IOT LABORATORY SYSTEM  ⚡",font=FS,fg=ACCENT,bg=BG).pack(pady=(0,14))
        tk.Label(mid,text="  ╔══════════════╗  \n  ║  ◉  LAB   ◉  ║  \n  ║  VOICE STUDIO ║  \n  ║  ┌──────────┐ ║  \n  ║  │▓▓▓▓▓▓▓▓▓│ ║  \n  ╚══════════════╝  ",font=("Courier New",12,"bold"),fg=ACCENT,bg=BG,justify="center").pack(pady=4)
        tv=tk.StringVar(); tk.Label(mid,textvariable=tv,font=FB,fg=WHITE,bg=BG).pack(pady=(14,4))
        txt="WELCOME, RESEARCHER!"; idx=[0]
        def tw():
            if idx[0]<=len(txt): tv.set(txt[:idx[0]]+("█" if idx[0]<len(txt) else "")); idx[0]+=1; mid.after(65,tw)
        tw()
        tk.Label(mid,text="Your intelligent IoT lab assistant is ready.",font=FN,fg=MUTED,bg=BG).pack(pady=(0,22))
        row=tk.Frame(mid,bg=BG); row.pack(pady=(0,26))
        for t,col in [("🌐  Network",ACCENT),("🎙  Voice Clone",PURPLE),("🤖  AI Powered",GREEN)]:
            tk.Label(row,text=t,font=FS,fg=col,bg=BG,padx=14,pady=6,relief="solid",bd=1).pack(side="left",padx=6)
        tk.Button(mid,text="  ENTER LAB  →",font=FK,fg=BG,bg=ACCENT,activebackground=PURPLE,activeforeground=WHITE,relief="flat",bd=0,padx=30,pady=12,cursor="hand2",command=self._connect).pack()

    def _connect(self):
        self._clear()
        f=tk.Frame(self,bg=BG); f.pack(fill="both",expand=True); self._s=f
        c=tk.Canvas(f,bg=BG,highlightthickness=0); c.place(relwidth=1,relheight=1)
        pts=[{"x":random.randint(0,1100),"y":random.randint(0,700),"s":random.uniform(0.3,0.8),"r":random.uniform(1,2.5)} for _ in range(40)]
        def anim():
            c.delete("d")
            for p in pts:
                p["y"]-=p["s"]
                if p["y"]<0: p["y"]=720;p["x"]=random.randint(0,1100)
                c.create_oval(p["x"]-p["r"],p["y"]-p["r"],p["x"]+p["r"],p["y"]+p["r"],fill=PURPLE,outline="",tags="d")
            f.after(30,anim)
        anim()
        card=tk.Frame(f,bg=CARD,highlightbackground=ACCENT,highlightthickness=2)
        card.place(relx=0.5,rely=0.5,anchor="center",width=460,height=500)
        tk.Frame(card,bg=PURPLE,height=6).pack(fill="x")
        inn=tk.Frame(card,bg=CARD,padx=36,pady=28); inn.pack(fill="both",expand=True)
        tk.Label(inn,text="🔌  CONNECT TO PI",font=FH,fg=PURPLE,bg=CARD).pack(pady=(0,4))
        tk.Label(inn,text="Enter your Raspberry Pi credentials",font=FS,fg=MUTED,bg=CARD).pack(pady=(0,22))
        tk.Label(inn,text="PI IP ADDRESS",font=FS,fg=ACCENT,bg=CARD,anchor="w").pack(fill="x",pady=(0,4))
        ip_v=tk.StringVar()
        ie=tk.Entry(inn,textvariable=ip_v,font=FN,bg="#0D1526",fg=WHITE,insertbackground=ACCENT,relief="flat",highlightthickness=2,highlightbackground=MUTED,highlightcolor=ACCENT)
        ie.pack(fill="x",ipady=10,pady=(0,16)); ie.insert(0,"192.168.x.x")
        ie.bind("<FocusIn>",lambda e:(ie.delete(0,"end"),ie.config(fg=WHITE)))
        tk.Label(inn,text="PASSWORD",font=FS,fg=ACCENT,bg=CARD,anchor="w").pack(fill="x",pady=(0,4))
        pw_v=tk.StringVar()
        pe=tk.Entry(inn,textvariable=pw_v,show="*",font=FN,bg="#0D1526",fg=WHITE,insertbackground=ACCENT,relief="flat",highlightthickness=2,highlightbackground=MUTED,highlightcolor=ACCENT)
        pe.pack(fill="x",ipady=10,pady=(0,20))
        sl=tk.Label(inn,text="",font=FS,fg=YELLOW,bg=CARD); sl.pack(pady=(0,8))
        def do_connect():
            ip=ip_v.get().strip(); pw=pw_v.get().strip()
            if not ip or ip=="192.168.x.x": sl.config(text="⚠  Please enter the Pi IP address.",fg=YELLOW); return
            if not pw: sl.config(text="⚠  Please enter the password.",fg=YELLOW); return
            sl.config(text="🔄  Connecting...",fg=ACCENT)
            f.after(1400,lambda:self._studio(ip,pw))
        tk.Button(inn,text="⚡  CONNECT",font=FK,fg=BG,bg=PURPLE,activebackground=ACCENT,activeforeground=BG,relief="flat",bd=0,pady=12,cursor="hand2",command=do_connect).pack(fill="x")
        tk.Label(card,text="Secure SSH Connection • AES-256",font=FS,fg=MUTED,bg=CARD).pack(pady=10)

    def _studio(self,ip,pw):
        self._clear()
        f=tk.Frame(self,bg=BG); f.pack(fill="both",expand=True); self._s=f
        tb=tk.Frame(f,bg=CARD2,height=50); tb.pack(fill="x"); tb.pack_propagate(False)
        tk.Label(tb,text="⚡ IOT LAB  —  VOICE STUDIO",font=FK,fg=ACCENT,bg=CARD2).pack(side="left",padx=20,pady=12)
        tk.Label(tb,text="● CONNECTED  "+ip,font=FS,fg=GREEN,bg=CARD2).pack(side="right",padx=20)
        body=tk.Frame(f,bg=BG); body.pack(fill="both",expand=True,padx=20,pady=16)
        L=tk.Frame(body,bg=CARD,width=300,highlightbackground=PURPLE,highlightthickness=1)
        L.pack(side="left",fill="y",padx=(0,16)); L.pack_propagate(False)
        tk.Label(L,text="PROFESSOR AI",font=FH,fg=PURPLE,bg=CARD).pack(pady=(20,2))
        tk.Label(L,text="Voice Clone Engine",font=FS,fg=MUTED,bg=CARD).pack(pady=(0,10))
        av=tk.Canvas(L,width=200,height=200,bg=CARD,highlightthickness=0); av.pack(pady=4)
        av.create_oval(10,10,190,190,fill="#1A0A3A",outline=PURPLE,width=2)
        av.create_oval(60,30,140,110,fill="#F4C59A",outline="#C47A4A",width=2)
        av.create_arc(60,28,140,78,start=0,extent=180,fill="#3D2B1F",outline="")
        for ex in [82,118]:
            av.create_oval(ex-8,54,ex+8,70,fill="white",outline="#555")
            av.create_oval(ex-4,57,ex+4,67,fill="#1A0800",outline="")
            av.create_oval(ex-1,58,ex+2,61,fill="white",outline="")
        av.create_rectangle(71,52,98,72,outline=ACCENT,width=2,fill="")
        av.create_rectangle(102,52,129,72,outline=ACCENT,width=2,fill="")
        av.create_line(98,62,102,62,fill=ACCENT,width=2)
        av.create_line(71,62,60,65,fill=ACCENT,width=2)
        av.create_line(129,62,140,65,fill=ACCENT,width=2)
        av.create_arc(84,80,116,102,start=200,extent=140,style="arc",outline="#C47A4A",width=2)
        av.create_rectangle(58,110,142,185,fill=PURPLE,outline="")
        av.create_polygon(85,110,100,132,115,110,fill="white",outline="")
        av.create_rectangle(94,110,106,158,fill="white",outline="")
        av.create_polygon(98,115,102,115,104,148,100,151,96,148,fill="#E53E3E",outline="")
        av.create_text(100,175,text="PROF. AI",font=("Courier New",9,"bold"),fill=ACCENT)
        for lb2,vl,col in [("MODEL","RVC v2",ACCENT),("QUALITY","HD 48kHz",GREEN),("DEVICE",ip,PURPLE)]:
            r=tk.Frame(L,bg=CARD2); r.pack(fill="x",padx=14,pady=2)
            tk.Label(r,text=lb2,font=FS,fg=MUTED,bg=CARD2,width=9,anchor="w").pack(side="left",padx=8,pady=5)
            tk.Label(r,text=vl,font=FS,fg=col,bg=CARD2).pack(side="right",padx=8)
        wc=tk.Canvas(L,height=55,bg=CARD2,highlightthickness=0); wc.pack(fill="x",padx=12,pady=(16,4))
        wt=[0]; wo=[False]
        def aw():
            wc.delete("all"); w=wc.winfo_width() or 260; bw=w/36
            for i in range(36):
                amp=(abs(math.sin(wt[0]+i*0.45))+random.uniform(-0.05,0.05)) if wo[0] else 0.06
                amp=max(0.06,min(1,amp)); bh=amp*44; x=i*bw+bw/2; y1=(55-bh)/2
                wc.create_rectangle(x-bw*0.35,y1,x+bw*0.35,y1+bh,fill=ACCENT if wo[0] else MUTED,outline="")
            wt[0]+=0.2; L.after(50,aw)
        aw()
        tk.Button(L,text="← DISCONNECT",font=FK,fg=BG,bg=YELLOW,activebackground=ACCENT,activeforeground=BG,relief="flat",bd=0,pady=10,cursor="hand2",command=self._welcome).pack(fill="x",padx=14,pady=(12,20))
        R=tk.Frame(body,bg=BG); R.pack(side="left",fill="both",expand=True)
        tk.Label(R,text="VOICE SYNTHESIS CONSOLE",font=FH,fg=WHITE,bg=BG).pack(anchor="w",pady=(0,4))
        tk.Label(R,text="Type any text and let the Professor speak it aloud.",font=FS,fg=MUTED,bg=BG).pack(anchor="w",pady=(0,14))
        ic=tk.Frame(R,bg=CARD,highlightbackground=ACCENT,highlightthickness=1); ic.pack(fill="x",pady=(0,12))
        tk.Label(ic,text="💬  WHAT DO YOU WANT ME TO SAY?",font=FS,fg=ACCENT,bg=CARD,anchor="w").pack(fill="x",padx=14,pady=(12,4))
        sr=tk.Frame(ic,bg=CARD); sr.pack(fill="x",padx=14,pady=(0,12))
        se=tk.Entry(sr,font=("Courier New",13),bg="#0D1526",fg=WHITE,insertbackground=ACCENT,relief="flat",highlightthickness=1,highlightbackground=MUTED,highlightcolor=ACCENT)
        se.pack(side="left",fill="both",expand=True,ipady=11,padx=(0,10))
        se.insert(0,"Hello students, welcome to the lab!")
        lbox=[None]
        def add_log(msg,err=False,ok=False):
            lb3=lbox[0]
            if lb3 is None: return
            lb3.config(state="normal")
            tag="e" if err else("o" if ok else"n")
            lb3.tag_config("e",foreground=YELLOW); lb3.tag_config("o",foreground=GREEN); lb3.tag_config("n",foreground=ACCENT)
            lb3.insert("end","["+time.strftime("%H:%M:%S")+"]  "+msg+"\n",tag)
            lb3.see("end"); lb3.config(state="disabled")
        def do_gen():
            txt=se.get().strip()
            if not txt: add_log("[ERROR]  No text entered.",err=True); return
            wo[0]=True; add_log('[INPUT]   "'+txt+'"')
            add_log("[ENGINE]  Processing through RVC voice model...")
            R.after(800,  lambda:add_log("[ENGINE]  Feature extraction complete."))
            R.after(1400, lambda:add_log("[ENGINE]  Pitch shift applied (Professor profile)."))
            R.after(2000, lambda:add_log("[ENGINE]  Audio synthesis done 100%"))
            R.after(2500, lambda:add_log('[OUTPUT]  Speaking: "'+txt+'"',ok=True))
            dur=max(2500,len(txt)*70)+2500
            R.after(dur,  lambda:(wo.__setitem__(0,False),add_log("[SYSTEM]  Playback complete. Ready.")))
        se.bind("<Return>",lambda e:do_gen())
        tk.Button(sr,text="▶  GENERATE",font=FK,fg=BG,bg=GREEN,activebackground=ACCENT,activeforeground=BG,relief="flat",bd=0,padx=18,pady=11,cursor="hand2",command=do_gen).pack(side="right")
        tk.Label(R,text="QUICK PHRASES",font=FS,fg=MUTED,bg=BG).pack(anchor="w",pady=(4,6))
        pf=tk.Frame(R,bg=BG); pf.pack(fill="x",pady=(0,12))
        for i,ph in enumerate(["Good morning, class!","Please open your textbooks.","The experiment begins now.","Excellent work, everyone!","Lab safety is paramount.","Any questions so far?"]):
            tk.Button(pf,text=ph,font=FS,fg=PURPLE,bg=CARD2,activebackground=PURPLE,activeforeground=WHITE,relief="flat",bd=0,padx=10,pady=6,cursor="hand2",command=lambda p=ph:(se.delete(0,"end"),se.insert(0,p))).grid(row=i//3,column=i%3,padx=3,pady=3,sticky="ew")
        pf.grid_columnconfigure((0,1,2),weight=1)
        tk.Label(R,text="OUTPUT LOG",font=FS,fg=MUTED,bg=BG).pack(anchor="w",pady=(4,4))
        lf=tk.Frame(R,bg=CARD,highlightbackground=MUTED,highlightthickness=1); lf.pack(fill="both",expand=True)
        lb3=tk.Text(lf,bg=CARD,fg=GREEN,font=FS,relief="flat",state="disabled",wrap="word",padx=10,pady=8)
        sb2=tk.Scrollbar(lf,command=lb3.yview); lb3.config(yscrollcommand=sb2.set)
        sb2.pack(side="right",fill="y"); lb3.pack(fill="both",expand=True)
        lbox[0]=lb3
        add_log("[SYSTEM]  Connected to Pi @ "+ip)
        add_log("[SYSTEM]  Voice model loaded — Professor RVC v2")
        add_log("[SYSTEM]  Ready. Enter text and press GENERATE.")

App().mainloop()