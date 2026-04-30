#!/usr/bin/env python3
"""
Script principal para disparar Newsletter LogSense com Parceria Olhar Digital

Uso:
    python send_newsletter.py --email usuario@exemplo.com
    python send_newsletter.py --batch emails.txt
    python send_newsletter.py --test
"""

import argparse
import sys
from pathlib import Path
from typing import List

# Adiciona o diretório src ao path para importações
sys.path.append(str(Path(__file__).parent / "src"))

from src.newsletter.newsletter_manager import NewsletterManager


def load_emails_from_file(file_path: str) -> List[str]:
    """Carrega lista de emails de um arquivo texto"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            emails = [line.strip() for line in f if line.strip() and '@' in line]
        return emails
    except FileNotFoundError:
        print(f"❌ Arquivo não encontrado: {file_path}")
        return []
    except Exception as e:
        print(f"❌ Erro ao ler arquivo {file_path}: {e}")
        return []


def validate_email(email: str) -> bool:
    """Validação básica de email"""
    return '@' in email and '.' in email.split('@')[-1]


def send_single_email(manager: NewsletterManager, email: str) -> bool:
    """Envia newsletter para um único email"""
    if not validate_email(email):
        print(f"❌ Email inválido: {email}")
        return False
    
    print(f"📧 Enviando newsletter para: {email}")
    success = manager.send_newsletter(email)
    
    if success:
        print(f"✅ Sucesso: {email}")
    else:
        print(f"❌ Falha: {email}")
    
    return success


def send_batch_emails(manager: NewsletterManager, emails: List[str]) -> None:
    """Envia newsletter em lote"""
    print(f"📊 Iniciando envio em lote para {len(emails)} emails...")
    
    # Validação dos emails
    valid_emails = [email for email in emails if validate_email(email)]
    invalid_emails = len(emails) - len(valid_emails)
    
    if invalid_emails > 0:
        print(f"⚠️  {invalid_emails} emails inválidos serão ignorados")
    
    # Envio
    results = manager.send_bulk_newsletter(valid_emails)
    
    # Estatísticas
    success_count = sum(results.values())
    failure_count = len(results) - success_count
    
    print(f"\n📈 Estatísticas do envio:")
    print(f"✅ Sucesso: {success_count}")
    print(f"❌ Falha: {failure_count}")
    print(f"📊 Total: {len(results)}")
    
    if failure_count > 0:
        print(f"\n❌ Emails com falha:")
        for email, success in results.items():
            if not success:
                print(f"   - {email}")


def test_newsletter(manager: NewsletterManager) -> None:
    """Testa o sistema de newsletter"""
    print("🧪 Iniciando teste do sistema de newsletter...")
    
    # Testa busca de notícias do Olhar Digital
    print("\n📰 Testando busca de notícias do Olhar Digital...")
    olhar_news = manager.fetch_olhar_digital_news(max_articles=2)
    print(f"✅ Encontradas {len(olhar_news)} notícias do Olhar Digital")
    
    for i, news in enumerate(olhar_news, 1):
        print(f"   {i}. {news['title'][:50]}...")
    
    # Testa busca de notícias adicionais
    print("\n📰 Testando busca de notícias adicionais...")
    additional_news = manager.fetch_additional_news(max_articles=2)
    print(f"✅ Encontradas {len(additional_news)} notícias adicionais")
    
    # Testa preparação de conteúdo
    print("\n📧 Testando preparação de conteúdo...")
    test_email = "test@example.com"
    content = manager.prepare_newsletter_content(test_email)
    print(f"✅ Conteúdo preparado para {test_email}")
    print(f"   - Total de artigos: {len(content['articles'])}")
    print(f"   - Notícias Olhar Digital: {content['olhar_count']}")
    
    # Testa geração de HTML
    print("\n🎨 Testando geração de HTML...")
    html = manager.generate_html_template(content)
    print(f"✅ HTML gerado ({len(html)} caracteres)")
    
    # Salva HTML para visualização
    output_file = Path("test_newsletter.html")
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html)
    print(f"💾 HTML salvo em: {output_file}")
    
    print("\n🎉 Teste concluído com sucesso!")


def main():
    """Função principal"""
    parser = argparse.ArgumentParser(
        description="Sistema de Newsletter LogSense com Parceria Olhar Digital",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos de uso:
  %(prog)s --email usuario@exemplo.com
  %(prog)s --batch emails.txt
  %(prog)s --test
  %(prog)s --emails email1@exemplo.com email2@exemplo.com
        """
    )
    
    parser.add_argument(
        "--email", 
        help="Email único para enviar a newsletter"
    )
    
    parser.add_argument(
        "--batch", 
        help="Arquivo com lista de emails (um por linha)"
    )
    
    parser.add_argument(
        "--emails", 
        nargs="+", 
        help="Lista de emails separados por espaço"
    )
    
    parser.add_argument(
        "--test", 
        action="store_true", 
        help="Executa testes do sistema sem enviar emails"
    )
    
    parser.add_argument(
        "--config", 
        default="config/newsletter_config.json",
        help="Arquivo de configuração (padrão: config/newsletter_config.json)"
    )
    
    args = parser.parse_args()
    
    # Verifica se foi fornecida alguma ação
    if not any([args.email, args.batch, args.emails, args.test]):
        parser.print_help()
        print("\n❌ Nenhuma ação especificada!")
        return
    
    # Inicializa o gerenciador
    try:
        manager = NewsletterManager(config_file=args.config)
        print("🚀 Gerenciador de newsletter inicializado com sucesso")
    except Exception as e:
        print(f"❌ Erro ao inicializar gerenciador: {e}")
        return
    
    # Executa a ação solicitada
    if args.test:
        test_newsletter(manager)
    
    elif args.email:
        send_single_email(manager, args.email)
    
    elif args.batch:
        emails = load_emails_from_file(args.batch)
        if emails:
            send_batch_emails(manager, emails)
        else:
            print("❌ Nenhum email válido encontrado no arquivo")
    
    elif args.emails:
        send_batch_emails(manager, args.emails)


if __name__ == "__main__":
    main()
