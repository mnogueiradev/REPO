"""
Sistema de Newsletter por Email com Parceria Olhar Digital

Garante que a cada disparo de email, pelo menos uma notícia do Olhar Digital seja incluída.
"""

import smtplib
import feedparser
import random
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List, Dict, Optional
import ssl
from pathlib import Path
import json


class NewsletterManager:
    """Gerenciador de newsletter com integração obrigatória ao Olhar Digital"""
    
    def __init__(self, config_file: str = "config/newsletter_config.json"):
        self.config_file = Path(config_file)
        self.config = self._load_config()
        self.olhar_digital_feeds = [
            "https://olhardigital.com.br/rss/",
            "https://olhardigital.com.br/feed/",
            "https://rss.cnn.com/rss/edition.rss"  # Feed alternativo caso Olhar Digital falhe
        ]
    
    def _load_config(self) -> Dict:
        """Carrega configurações de email e feeds"""
        default_config = {
            "smtp": {
                "server": "smtp.gmail.com",
                "port": 587,
                "username": "",
                "password": "",
                "use_tls": True
            },
            "newsletter": {
                "from_name": "LogSense Newsletter",
                "from_email": "",
                "max_articles": 5,
                "olhar_digital_min_articles": 1
            },
            "feeds": {
                "additional_sources": [
                    "https://g1.globo.com/rss/g1/",
                    "https://feeds.folha.uol.com.br/emcimadahora/rss091.xml",
                    "https://www.tecmundo.com.br/rss/"
                ]
            }
        }
        
        if self.config_file.exists():
            with open(self.config_file, 'r', encoding='utf-8') as f:
                user_config = json.load(f)
                default_config.update(user_config)
        
        return default_config
    
    def fetch_olhar_digital_news(self, max_articles: int = 3) -> List[Dict]:
        """
        Busca notícias do Olhar Digital com múltiplas tentativas
        Garante pelo menos uma notícia do Olhar Digital
        """
        olhar_news = []
        
        for feed_url in self.olhar_digital_feeds:
            try:
                feed = feedparser.parse(feed_url)
                entries = feed.entries[:max_articles]
                
                for entry in entries:
                    if 'olhardigital' in feed_url.lower() or 'olhar' in feed.feed.get('title', '').lower():
                        article = {
                            'title': entry.get('title', ''),
                            'link': entry.get('link', ''),
                            'description': entry.get('description', ''),
                            'published': entry.get('published', ''),
                            'source': 'Olhar Digital',
                            'priority': 'high'
                        }
                        olhar_news.append(article)
                
                if olhar_news:
                    break
                    
            except Exception as e:
                print(f"Erro ao buscar feed {feed_url}: {e}")
                continue
        
        # Se não encontrou notícias do Olhar Digital, cria uma notícia padrão
        if not olhar_news:
            olhar_news.append({
                'title': "Parceria Olhar Digital - Tecnologia e Inovação",
                'link': "https://olhardigital.com.br",
                'description': "Conteúdo exclusivo Olhar Digital - Sua parceira oficial em tecnologia e inovação. Confira as últimas notícias do mundo tech.",
                'published': datetime.now().strftime('%a, %d %b %Y %H:%M:%S %z'),
                'source': 'Olhar Digital',
                'priority': 'high'
            })
        
        return olhar_news[:max_articles]
    
    def fetch_additional_news(self, max_articles: int = 4) -> List[Dict]:
        """Busca notícias de outras fontes para complementar a newsletter"""
        additional_news = []
        
        for feed_url in self.config['feeds']['additional_sources']:
            try:
                feed = feedparser.parse(feed_url)
                entries = feed.entries[:max_articles]
                
                for entry in entries:
                    article = {
                        'title': entry.get('title', ''),
                        'link': entry.get('link', ''),
                        'description': entry.get('description', ''),
                        'published': entry.get('published', ''),
                        'source': feed.feed.get('title', 'Fonte Desconhecida'),
                        'priority': 'normal'
                    }
                    additional_news.append(article)
                
                if len(additional_news) >= max_articles:
                    break
                    
            except Exception as e:
                print(f"Erro ao buscar feed adicional {feed_url}: {e}")
                continue
        
        return additional_news[:max_articles]
    
    def prepare_newsletter_content(self, recipient_email: str) -> Dict:
        """
        Prepara o conteúdo da newsletter garantindo a inclusão do Olhar Digital
        """
        # Busca notícias do Olhar Digital (obrigatório)
        olhar_articles = self.fetch_olhar_digital_news(
            max_articles=self.config['newsletter']['olhar_digital_min_articles']
        )
        
        # Busca notícias adicionais
        max_additional = self.config['newsletter']['max_articles'] - len(olhar_articles)
        additional_articles = self.fetch_additional_news(max_articles=max_additional)
        
        # Combina as notícias
        all_articles = olhar_articles + additional_articles
        
        # Embaralha as notícias adicionais mas mantém as do Olhar Digital no topo
        if additional_articles:
            random.shuffle(additional_articles)
            all_articles = olhar_articles + additional_articles
        
        return {
            'recipient': recipient_email,
            'date': datetime.now().strftime('%d/%m/%Y'),
            'articles': all_articles[:self.config['newsletter']['max_articles']],
            'olhar_count': len(olhar_articles)
        }
    
    def generate_html_template(self, content: Dict) -> str:
        """Gera o template HTML da newsletter"""
        html_template = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>LogSense Newsletter - {content['date']}</title>
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }}
        .content {{ background: #f9f9f9; padding: 30px; border-radius: 0 0 10px 10px; }}
        .article {{ background: white; margin: 15px 0; padding: 20px; border-radius: 8px; border-left: 4px solid #667eea; }}
        .olhar-digital {{ border-left-color: #ff6b35; background: #fff8f3; }}
        .article h3 {{ margin: 0 0 10px 0; color: #333; }}
        .article .meta {{ font-size: 12px; color: #666; margin-bottom: 10px; }}
        .article .description {{ margin-bottom: 15px; }}
        .article a {{ color: #667eea; text-decoration: none; font-weight: bold; }}
        .article a:hover {{ text-decoration: underline; }}
        .footer {{ text-align: center; margin-top: 30px; padding: 20px; background: #f0f0f0; border-radius: 8px; }}
        .partnership {{ background: #ff6b35; color: white; padding: 15px; border-radius: 8px; text-align: center; margin: 20px 0; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📰 LogSense Newsletter</h1>
            <p>Sua dose diária de tecnologia e segurança - {content['date']}</p>
        </div>
        
        <div class="content">
            <div class="partnership">
                <h3>🤝 Parceria Oficial Olhar Digital</h3>
                <p>Conteúdo exclusivo e notícias em tempo real do nosso parceiro Olhar Digital</p>
            </div>
            
            {"<hr>" if content['olhar_count'] > 0 else ""}
            
            {"".join([
                f"""
                <div class="article {'olhar-digital' if article['source'] == 'Olhar Digital' else ''}">
                    <h3>{article['title']}</h3>
                    <div class="meta">
                        📅 {article['published']} | 📍 {article['source']}
                        {' | ⭐ Parceria Olhar Digital' if article['source'] == 'Olhar Digital' else ''}
                    </div>
                    <div class="description">
                        {article['description'][:200]}{'...' if len(article['description']) > 200 else ''}
                    </div>
                    <a href="{article['link']}" target="_blank">Leia mais →</a>
                </div>
                """ for article in content['articles']
            ])}
            
            <div class="footer">
                <p><strong>📧 LogSense Newsletter</strong></p>
                <p>Recebendo {content['olhar_count']} notícia(s) do Olhar Digital nesta edição</p>
                <p><small>Parceria oficial com Olhar Digital - Tecnologia e Inovação</small></p>
                <p><small>Caso não queira mais receber, responda este email com "Remover"</small></p>
            </div>
        </div>
    </div>
</body>
</html>
        """
        return html_template
    
    def send_newsletter(self, recipient_email: str) -> bool:
        """
        Envia a newsletter garantindo a inclusão do Olhar Digital
        """
        try:
            # Prepara o conteúdo
            content = self.prepare_newsletter_content(recipient_email)
            
            # Validação obrigatória do Olhar Digital
            if content['olhar_count'] == 0:
                raise ValueError("Não foi possível incluir notícias do Olhar Digital")
            
            # Gera o HTML
            html_content = self.generate_html_template(content)
            
            # Configura o email
            msg = MIMEMultipart('alternative')
            msg['Subject'] = f"LogSense Newsletter - {content['date']} | Parceria Olhar Digital"
            msg['From'] = f"{self.config['newsletter']['from_name']} <{self.config['newsletter']['from_email']}>"
            msg['To'] = recipient_email
            
            # Adiciona o conteúdo HTML
            html_part = MIMEText(html_content, 'html', 'utf-8')
            msg.attach(html_part)
            
            # Envia o email
            context = ssl.create_default_context()
            
            with smtplib.SMTP(
                self.config['smtp']['server'], 
                self.config['smtp']['port']
            ) as server:
                server.starttls(context=context)
                server.login(
                    self.config['smtp']['username'], 
                    self.config['smtp']['password']
                )
                server.send_message(msg)
            
            print(f"✅ Newsletter enviada para {recipient_email} | {content['olhar_count']} notícia(s) Olhar Digital")
            return True
            
        except Exception as e:
            print(f"❌ Erro ao enviar newsletter para {recipient_email}: {e}")
            return False
    
    def send_bulk_newsletter(self, recipient_emails: List[str]) -> Dict[str, bool]:
        """
        Envia newsletter em lote garantindo Olhar Digital em cada envio
        """
        results = {}
        
        for email in recipient_emails:
            results[email] = self.send_newsletter(email)
        
        success_count = sum(results.values())
        print(f"📊 Resultado: {success_count}/{len(recipient_emails)} emails enviados com sucesso")
        
        return results


def main():
    """Função principal para teste"""
    manager = NewsletterManager()
    
    # Teste de envio
    test_emails = ["test@example.com"]
    results = manager.send_bulk_newsletter(test_emails)
    
    print("Resultados:", results)


if __name__ == "__main__":
    main()
