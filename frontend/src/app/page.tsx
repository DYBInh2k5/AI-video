'use client';

import { useState, useEffect } from 'react';
import axios from 'axios';
import { Upload, Languages, Play, Download, CheckCircle, Loader2, Sparkles } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

const LANGUAGES = [
  { code: 'vi', name: 'Vietnamese' },
  { code: 'en', name: 'English' },
  { code: 'ja', name: 'Japanese' },
  { code: 'ko', name: 'Korean' },
  { code: 'fr', name: 'French' },
  { code: 'es', name: 'Spanish' },
  { code: 'de', name: 'German' },
];

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export default function Home() {
  const [file, setFile] = useState<File | null>(null);
  const [videoId, setVideoId] = useState<string | null>(null);
  const [targetLang, setTargetLang] = useState('en');
  const [status, setStatus] = useState<'idle' | 'uploading' | 'processing' | 'completed' | 'failed'>('idle');
  const [progress, setProgress] = useState(0);
  const [resultUrl, setResultUrl] = useState<string | null>(null);

  const handleUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    if (!e.target.files?.[0]) return;
    const selectedFile = e.target.files[0];
    setFile(selectedFile);
    setStatus('uploading');

    const formData = new FormData();
    formData.append('file', selectedFile);

    try {
      const res = await axios.post(`${API_URL}/upload`, formData);
      setVideoId(res.data.video_id);
      setStatus('idle');
    } catch (err) {
      console.error(err);
      setStatus('failed');
    }
  };

  const startTranslation = async () => {
    if (!videoId) return;
    setStatus('processing');
    setProgress(10);

    try {
      await axios.post(`${API_URL}/translate`, {
        video_id: videoId,
        target_language: targetLang
      });

      // Poll for status
      const interval = setInterval(async () => {
        const res = await axios.get(`${API_URL}/status/${videoId}`);
        if (res.data.status === 'completed') {
          setResultUrl(res.data.url);
          setStatus('completed');
          setProgress(100);
          clearInterval(interval);
        } else if (res.data.status === 'failed') {
          setStatus('failed');
          clearInterval(interval);
        } else if (res.data.status === 'processing') {
          setProgress((prev) => Math.min(prev + 5, 95));
        }
      }, 3000);
    } catch (err) {
      console.error(err);
      setStatus('failed');
    }
  };

  return (
    <div className="min-h-screen bg-slate-950 text-white selection:bg-indigo-500/30">
      {/* Navbar */}
      <nav className="border-b border-white/10 px-6 py-4 backdrop-blur-md sticky top-0 z-50">
        <div className="max-w-7xl mx-auto flex justify-between items-center">
          <div className="flex items-center gap-2 font-bold text-2xl tracking-tighter">
            <div className="w-8 h-8 bg-gradient-to-br from-indigo-500 to-purple-600 rounded-lg flex items-center justify-center">
              <Sparkles className="w-5 h-5" />
            </div>
            <span>AI Voice Clone Pro</span>
          </div>
          <div className="hidden md:flex gap-8 text-sm font-medium text-slate-400">
            <a href="#" className="hover:text-white transition-colors">Tính năng</a>
            <a href="#" className="hover:text-white transition-colors">Bảng giá (Free)</a>
            <a href="#" className="hover:text-white transition-colors">API</a>
          </div>
          <button className="bg-white text-black px-5 py-2 rounded-full text-sm font-bold hover:bg-slate-200 transition-colors">
            Bắt đầu ngay
          </button>
        </div>
      </nav>

      <main className="max-w-4xl mx-auto px-6 py-20">
        {/* Hero Section */}
        <div className="text-center mb-16">
          <motion.h1 
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="text-5xl md:text-7xl font-bold mb-6 bg-gradient-to-b from-white to-slate-400 bg-clip-text text-transparent"
          >
            Dịch Video & Clone Giọng Nói Tự Động
          </motion.h1>
          <motion.p 
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 }}
            className="text-xl text-slate-400 max-w-2xl mx-auto"
          >
            Tự động dịch ngôn ngữ từ video và lồng tiếng bằng chính giọng của bạn hoặc AI. 
            Mọi tính năng trả phí của ElevenLabs giờ đây đều miễn phí.
          </motion.p>
        </div>

        {/* Main Action Card */}
        <motion.div 
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ delay: 0.2 }}
          className="bg-slate-900 border border-white/10 rounded-3xl p-8 shadow-2xl shadow-indigo-500/10"
        >
          <div className="grid md:grid-cols-2 gap-10">
            {/* Left Side: Upload */}
            <div className="space-y-6">
              <h2 className="text-xl font-semibold flex items-center gap-2">
                <Upload className="w-5 h-5 text-indigo-400" />
                Bước 1: Tải video lên
              </h2>
              
              <div className="relative group">
                <input 
                  type="file" 
                  accept="video/*" 
                  onChange={handleUpload}
                  className="absolute inset-0 w-full h-full opacity-0 cursor-pointer z-10"
                />
                <div className="border-2 border-dashed border-white/10 group-hover:border-indigo-500/50 rounded-2xl p-10 text-center transition-all bg-slate-800/50">
                  {file ? (
                    <div className="space-y-2">
                      <CheckCircle className="w-10 h-10 text-green-400 mx-auto" />
                      <p className="font-medium text-slate-200">{file.name}</p>
                      <p className="text-xs text-slate-500">{(file.size / 1024 / 1024).toFixed(2)} MB</p>
                    </div>
                  ) : (
                    <div className="space-y-2">
                      <div className="w-12 h-12 bg-indigo-500/10 rounded-full flex items-center justify-center mx-auto group-hover:scale-110 transition-transform">
                        <Upload className="w-6 h-6 text-indigo-400" />
                      </div>
                      <p className="text-slate-300 font-medium">Kéo thả video vào đây</p>
                      <p className="text-xs text-slate-500">MP4, MOV lên đến 100MB</p>
                    </div>
                  )}
                </div>
              </div>
            </div>

            {/* Right Side: Options */}
            <div className="space-y-6">
              <h2 className="text-xl font-semibold flex items-center gap-2">
                <Languages className="w-5 h-5 text-purple-400" />
                Bước 2: Chọn ngôn ngữ
              </h2>

              <div className="space-y-4">
                <div>
                  <label className="text-xs text-slate-500 uppercase tracking-wider mb-2 block">Dịch sang</label>
                  <select 
                    value={targetLang}
                    onChange={(e) => setTargetLang(e.target.value)}
                    className="w-full bg-slate-800 border border-white/10 rounded-xl px-4 py-3 focus:outline-none focus:ring-2 focus:ring-indigo-500 transition-all appearance-none"
                  >
                    {LANGUAGES.map(lang => (
                      <option key={lang.code} value={lang.code}>{lang.name}</option>
                    ))}
                  </select>
                </div>

                <div className="pt-4">
                  <button 
                    onClick={startTranslation}
                    disabled={!videoId || status === 'processing'}
                    className="w-full bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-500 hover:to-purple-500 disabled:opacity-50 disabled:cursor-not-allowed text-white font-bold py-4 rounded-xl shadow-lg shadow-indigo-500/20 transition-all flex items-center justify-center gap-2"
                  >
                    {status === 'processing' ? (
                      <>
                        <Loader2 className="w-5 h-5 animate-spin" />
                        Đang xử lý {progress}%
                      </>
                    ) : (
                      <>
                        <Play className="w-5 h-5 fill-current" />
                        Bắt đầu dịch ngay
                      </>
                    )}
                  </button>
                </div>
              </div>
            </div>
          </div>

          {/* Result Area */}
          <AnimatePresence>
            {status === 'completed' && resultUrl && (
              <motion.div 
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                className="mt-10 pt-10 border-t border-white/10"
              >
                <div className="flex flex-col md:flex-row items-center gap-6 bg-indigo-500/5 rounded-2xl p-6 border border-indigo-500/20">
                  <div className="w-full md:w-1/3 aspect-video bg-slate-800 rounded-lg overflow-hidden relative">
                    <video src={resultUrl} className="w-full h-full object-cover" controls />
                  </div>
                  <div className="flex-1 space-y-2">
                    <h3 className="text-lg font-bold">Video của bạn đã sẵn sàng!</h3>
                    <p className="text-slate-400 text-sm">Chúng tôi đã hoàn thành việc dịch và lồng tiếng bằng AI.</p>
                    <div className="flex gap-3 pt-2">
                      <a 
                        href={resultUrl} 
                        download 
                        className="flex items-center gap-2 bg-white text-black px-4 py-2 rounded-lg text-sm font-bold hover:bg-slate-200 transition-colors"
                      >
                        <Download className="w-4 h-4" />
                        Tải về máy
                      </a>
                    </div>
                  </div>
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </motion.div>

        {/* Features Comparison */}
        <div className="mt-32">
          <h2 className="text-3xl font-bold text-center mb-12">Tại sao chọn chúng tôi?</h2>
          <div className="grid md:grid-cols-3 gap-8">
            {[
              { title: "Clone Giọng Nói", desc: "Giữ nguyên cảm xúc và tông giọng của người nói gốc.", icon: <Sparkles className="w-6 h-6" /> },
              { title: "Dịch Đa Ngôn Ngữ", desc: "Hỗ trợ hơn 29 ngôn ngữ phổ biến trên toàn thế giới.", icon: <Languages className="w-6 h-6" /> },
              { title: "Hoàn Toàn Miễn Phí", desc: "Không giới hạn ký tự, không bắt đăng ký trả phí.", icon: <CheckCircle className="w-6 h-6" /> }
            ].map((feature, i) => (
              <div key={i} className="p-6 rounded-2xl bg-white/5 border border-white/10 hover:bg-white/10 transition-colors">
                <div className="w-12 h-12 bg-indigo-500/20 rounded-xl flex items-center justify-center mb-4 text-indigo-400">
                  {feature.icon}
                </div>
                <h3 className="text-xl font-bold mb-2">{feature.title}</h3>
                <p className="text-slate-400 text-sm leading-relaxed">{feature.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer className="border-t border-white/10 mt-20 py-10 px-6 text-center text-slate-500 text-sm">
        <p>© 2026 AI Voice Clone Pro. Được phát triển để thay thế các dịch vụ trả phí đắt đỏ.</p>
      </footer>
    </div>
  );
}
